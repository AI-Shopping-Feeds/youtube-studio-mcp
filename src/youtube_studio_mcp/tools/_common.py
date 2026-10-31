from __future__ import annotations

import math
from typing import Any

import anyio.from_thread
from mcp.server.mcpserver import Context
from mcp.types import ToolAnnotations

from .._logging import get_logger

logger = get_logger("tools")

READ = ToolAnnotations(read_only_hint=True, open_world_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=True)
# Server-local tools (auth status, audit log, dry-run) never call YouTube.
LOCAL_READ = ToolAnnotations(read_only_hint=True, open_world_hint=False)
LOCAL_WRITE = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)


def require_confirm(confirm: bool, what: str) -> None:
    if not confirm:
        raise ValueError(f"{what} can't be undone. Call again with confirm=true to proceed.")


def merge(base: dict[str, Any], extra: dict[str, Any] | None) -> dict[str, Any]:
    """Add caller-supplied query parameters (e.g. onBehalfOfContentOwner) to `base`."""
    return {**base, **(extra or {})}


def parts_of(body: dict[str, Any], default: str = "snippet") -> str:
    """Derive the `part` parameter from the top-level keys of a resource body."""
    parts = [k for k in body if k not in ("id", "kind", "etag")]
    return ",".join(parts) or default


class ProgressReporter:
    """Send MCP progress notifications from a worker thread.

    Call it from code running under anyio.to_thread.run_sync. Values that don't
    increase are dropped (the spec requires strictly increasing progress), and it
    does nothing when the tool was called outside an MCP request. A failed
    notification is logged and never interrupts the work being reported.
    """

    def __init__(self, ctx: Context | None) -> None:
        try:
            self._ctx = ctx if ctx is not None and ctx.request_context else None
        except ValueError:  # no request context, e.g. MCPServer.call_tool in-process
            self._ctx = None
        self._last = -math.inf

    def __call__(self, progress: float, total: float | None = None, message: str | None = None):
        if self._ctx is None or progress <= self._last:
            return
        self._last = progress
        try:
            anyio.from_thread.run(self._ctx.report_progress, progress, total, message)
        except Exception as e:
            logger.debug("progress notification failed: %s", e)
