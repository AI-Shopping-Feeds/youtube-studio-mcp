from __future__ import annotations

from typing import Any

from mcp.types import ToolAnnotations

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True)


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
