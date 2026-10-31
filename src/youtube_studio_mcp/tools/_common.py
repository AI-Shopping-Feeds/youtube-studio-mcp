from __future__ import annotations

from typing import Any

from mcp.types import ToolAnnotations

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
