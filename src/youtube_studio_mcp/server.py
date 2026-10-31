"""Build the MCP server with every youtube_* tool registered."""

from __future__ import annotations

import functools
import inspect
from pathlib import Path
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from . import __version__
from ._logging import configure_default, get_logger
from .audit import AuditLog
from .auth import SCOPES, OAuthUserAuth
from .client import YouTubeAPIError, YouTubeClient
from .config import Config, load_config
from .tools import MODULES
from .tools._common import LOCAL_READ, LOCAL_WRITE

logger = get_logger("server")

# Errors whose message helps the agent fix the call (bad arguments, a refusal
# such as a missing confirm=true, quota, permissions or config problems).
_EXPECTED_ERRORS = (
    ValueError,
    RuntimeError,
    PermissionError,
    FileNotFoundError,
    YouTubeAPIError,
    httpx.HTTPError,
)


def _as_tool_error(fn):
    """Re-raises expected errors as ToolError so MCP SDK 2 shows their message.

    SDK 2 hides the text of any other exception from the client.
    """
    if inspect.iscoroutinefunction(fn):

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except _EXPECTED_ERRORS as exc:
                raise ToolError(str(exc)) from exc

        return async_wrapper

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except _EXPECTED_ERRORS as exc:
            raise ToolError(str(exc)) from exc

    return wrapper


class YouTubeMCPServer(MCPServer):
    """MCPServer whose tools report expected errors to the client."""

    def tool(self, *args: Any, **kwargs: Any):
        register = super().tool(*args, **kwargs)
        return lambda fn: register(_as_tool_error(fn))


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
) -> MCPServer:
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

    mcp = YouTubeMCPServer("youtube-studio-mcp", version=__version__, instructions=INSTRUCTIONS)

    @mcp.tool(annotations=LOCAL_READ)
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

    @mcp.tool(annotations=LOCAL_READ)
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

    @mcp.tool(annotations=LOCAL_READ)
    def youtube_audit_tail(limit: int = 20) -> dict[str, Any]:
        """Show the most recent write operations from the audit log."""
        entries = audit.tail(limit)
        return {"count": len(entries), "entries": entries}

    @mcp.tool(annotations=LOCAL_READ)
    def youtube_audit_lookup(audit_id: str) -> dict[str, Any]:
        """Look up one audit log entry by ID."""
        entry = audit.find(audit_id)
        return {"found": entry is not None, "audit_id": audit_id, "entry": entry}

    @mcp.tool(annotations=LOCAL_WRITE)
    def youtube_set_dry_run(enabled: bool) -> dict[str, Any]:
        """Turn dry-run on or off for this session. In dry-run, writes and uploads are logged
        to the audit log but not sent to YouTube."""
        config.dry_run = enabled
        return {"dry_run": enabled}

    for module in MODULES:
        module.register(mcp, client)
    return mcp
