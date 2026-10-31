from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

CHUNK_GRANULARITY = 256 * 1024  # resumable chunks must be multiples of 256 KiB


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


@dataclass
class Config:
    client_secrets: Path
    token_file: Path
    audit_log: Path
    upload_dir: Path | None = None
    dry_run: bool = False
    timeout: float = 60.0
    upload_chunk_size: int = 8 * 1024 * 1024
    page_size: int = 50
    log_level: str = "INFO"
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000


def load_config(env_file: Path | None = None) -> Config:
    """Read configuration from the environment (and an optional .env file).

    Credentials are not checked here, so the server can start and report
    auth status even before `youtube-studio-mcp auth-init` has been run.
    """
    load_dotenv(dotenv_path=env_file, override=False)

    def _number(name: str, default: str, cast: type) -> float | int:
        raw = os.environ.get(name, default)
        try:
            return cast(raw)
        except ValueError as e:
            raise RuntimeError(f"{name} must be a number, got '{raw}'.") from e

    chunk_mb = _number("YOUTUBE_UPLOAD_CHUNK_MB", "8", float)
    chunk = max(1, int(chunk_mb * 1024 * 1024) // CHUNK_GRANULARITY) * CHUNK_GRANULARITY

    transport = os.environ.get("YOUTUBE_TRANSPORT", "stdio").strip().lower()
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise RuntimeError(
            f"YOUTUBE_TRANSPORT must be stdio, sse or streamable-http, got '{transport}'."
        )

    audit = _path(os.environ.get("YOUTUBE_AUDIT_LOG", "logs/audit.jsonl"))
    audit.parent.mkdir(parents=True, exist_ok=True)

    return Config(
        client_secrets=_path(
            os.environ.get("YOUTUBE_CLIENT_SECRETS", "secrets/client_secret.json")
        ),
        token_file=_path(os.environ.get("YOUTUBE_TOKEN_FILE", "secrets/token.json")),
        audit_log=audit,
        upload_dir=_path(os.environ["YOUTUBE_UPLOAD_DIR"])
        if os.environ.get("YOUTUBE_UPLOAD_DIR", "").strip()
        else None,
        dry_run=_truthy(os.environ.get("YOUTUBE_DRY_RUN")),
        timeout=float(_number("YOUTUBE_TIMEOUT", "60", float)),
        upload_chunk_size=chunk,
        page_size=int(_number("YOUTUBE_PAGE_SIZE", "50", int)),
        log_level=os.environ.get("YOUTUBE_LOG_LEVEL", "INFO").upper(),
        transport=transport,
        host=os.environ.get("YOUTUBE_HOST", "127.0.0.1"),
        port=int(_number("YOUTUBE_PORT", "8000", int)),
    )
