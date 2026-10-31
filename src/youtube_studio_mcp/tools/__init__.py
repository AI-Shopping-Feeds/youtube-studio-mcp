from __future__ import annotations

from collections.abc import Iterable
from types import ModuleType

from . import analytics, captions, channels, comments, live, playlists, raw, search, uploads, videos

MODULES = (channels, videos, uploads, playlists, comments, captions, search, live, analytics, raw)

# YOUTUBE_TOOL_GROUPS names: one group per tool module, in registration order.
GROUPS: dict[str, ModuleType] = {m.__name__.rsplit(".", 1)[-1]: m for m in MODULES}


def select_modules(groups: Iterable[str]) -> tuple[ModuleType, ...]:
    """Return the tool modules for the named groups (all of them when empty).

    Raises RuntimeError naming the valid groups if any name is unknown.
    """
    wanted = set(groups)
    unknown = sorted(wanted - set(GROUPS))
    if unknown:
        raise RuntimeError(
            f"Unknown YOUTUBE_TOOL_GROUPS value(s): {', '.join(unknown)}. "
            f"Valid groups: {', '.join(GROUPS)}."
        )
    if not wanted:
        return MODULES
    return tuple(module for name, module in GROUPS.items() if name in wanted)


__all__ = ["GROUPS", "MODULES", "select_modules"]
