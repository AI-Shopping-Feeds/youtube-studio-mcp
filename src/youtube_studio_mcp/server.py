"""Build the FastMCP server with every youtube_* tool registered."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import __version__
from ._logging import configure_default, get_logger
from .audit import AuditLog
from .auth import SCOPES, OAuthUserAuth
from .client import YouTubeClient
from .config import Config, load_config
from .tools import MODULES
from .tools._common import READ

logger = get_logger("server")

INSTRUCTIONS = """\
YouTube Studio MCP: manage a YouTube channel through the YouTube Data API v3,
YouTube Analytics API v2 and YouTube Reporting API v1.
- Upload videos with youtube_upload_video / youtube_upload_videos (local path or URL,
  never raw bytes). Uploads default to private. Poll youtube_get_upload_status.
- Quota: videos.insert and search.list have their own daily buckets (default 100 calls/day
  each); most writes cost 50 units of the 10,000/day main bucket.
- Deletes need confirm=true. Every write is audit-logged; set dry-run with youtube_set_dry_run.
- Use youtube_call_api for any method without a dedicated tool.
"""


def build_server(
    config: Config | None = None, env_file: Path | None = None, auth: Any | None = None
) -> FastMCP:
    configure_default()
    if config is None:
        config = load_config(env_file=env_file)

    if auth is None:
        auth = OAuthUserAuth(config.token_file, config.client_secrets)
    audit = AuditLog(config.audit_log)
    client = YouTubeClient(config, auth, audit)
    logger.info(
        "starting youtube-studio-mcp %s token=%s dry_run=%s",
        __version__,
        config.token_file,
        config.dry_run,
    )

    mcp = FastMCP("youtube-studio-mcp", instructions=INSTRUCTIONS)

    @mcp.tool(annotations=READ)
    def youtube_auth_status() -> dict[str, Any]:
        """Show whether OAuth credentials exist, which scopes were granted and how to sign in."""
        status = auth.status()
        status["requested_scopes"] = SCOPES
        if not status["token_exists"]:
            status["next_step"] = (
                "Run in a terminal: youtube-studio-mcp auth-init --client-secrets "
                f"{config.client_secrets} --output {config.token_file}"
            )
        return status

    @mcp.tool(annotations=READ)
    def youtube_describe_server() -> dict[str, Any]:
        """Show the server version, config, dry-run state and audit log location."""
        return {
            "version": __version__,
            "auth": auth.account_label,
            "token_file": str(config.token_file),
            "audit_log": str(config.audit_log),
            "dry_run": config.dry_run,
            "upload_chunk_bytes": config.upload_chunk_size,
            "timeout": config.timeout,
            "transport": config.transport,
        }

    @mcp.tool(annotations=READ)
    def youtube_audit_tail(limit: int = 20) -> dict[str, Any]:
        """Show the most recent write operations from the audit log."""
        entries = audit.tail(limit)
        return {"count": len(entries), "entries": entries}

    @mcp.tool(annotations=READ)
    def youtube_audit_lookup(audit_id: str) -> dict[str, Any]:
        """Look up one audit log entry by ID."""
        entry = audit.find(audit_id)
        return {"found": entry is not None, "audit_id": audit_id, "entry": entry}

    @mcp.tool()
    def youtube_set_dry_run(enabled: bool) -> dict[str, Any]:
        """Turn dry-run on or off for this session. In dry-run, writes and uploads are logged
        to the audit log but not sent to YouTube."""
        config.dry_run = enabled
        return {"dry_run": enabled}

    for module in MODULES:
        module.register(mcp, client)
    return mcp
