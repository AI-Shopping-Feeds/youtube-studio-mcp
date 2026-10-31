"""Resolve a media source (local path or http(s) URL) to a local file.

Tools take a path or URL, never file bytes: MCP tool arguments are JSON and
videos are far too large to pass inline.
"""

from __future__ import annotations

import mimetypes
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

from ._logging import get_logger

logger = get_logger("media")

EXTRA_TYPES = {
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".m4v": "video/x-m4v",
    ".srt": "application/x-subrip",
    ".vtt": "text/vtt",
    ".sbv": "text/plain",
}


def guess_mime(path: Path, fallback: str = "application/octet-stream") -> str:
    ext = path.suffix.lower()
    if ext in EXTRA_TYPES:
        return EXTRA_TYPES[ext]
    return mimetypes.guess_type(path.name)[0] or fallback


@contextmanager
def local_file(
    source: str, *, allowed_dir: Path | None = None, timeout: float = 600.0
) -> Iterator[Path]:
    """Yield a local Path for `source`. URLs are downloaded to a temp file that is
    deleted afterwards; local paths are used in place and, when `allowed_dir` is set
    (YOUTUBE_UPLOAD_DIR), must be inside it."""
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https"):
        suffix = Path(unquote(parsed.path)).suffix
        fd, tmp_name = tempfile.mkstemp(prefix="youtube-mcp-", suffix=suffix)
        tmp = Path(tmp_name)
        try:
            with (
                os.fdopen(fd, "wb") as out,
                httpx.stream("GET", source, follow_redirects=True, timeout=timeout) as resp,
            ):
                resp.raise_for_status()
                for block in resp.iter_bytes(1024 * 1024):
                    out.write(block)
            logger.info("downloaded %s to %s", source, tmp)
            yield tmp
        finally:
            tmp.unlink(missing_ok=True)
        return

    path = Path(unquote(parsed.path) if parsed.scheme == "file" else source).expanduser()
    if not path.is_file():
        raise RuntimeError(f"File not found: {path}")
    path = path.resolve()
    if allowed_dir is not None and not path.is_relative_to(allowed_dir):
        raise RuntimeError(f"{path} is outside YOUTUBE_UPLOAD_DIR ({allowed_dir}).")
    yield path
