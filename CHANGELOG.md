# Changelog

## 0.3.0 (unreleased)

Brings the server in line with current MCP best practice (MCP spec 2026-07-28, Python SDK 2.3).

### Added

- **Tool filtering:** `YOUTUBE_TOOL_GROUPS` (comma-separated: `channels`, `videos`, `uploads`,
  `playlists`, `comments`, `captions`, `search`, `live`, `analytics`, `raw`; empty means all)
  and `YOUTUBE_READ_ONLY=true` (read-only tools only). The auth, server, audit and dry-run
  tools are always registered. An unknown group stops the server at startup and lists the
  valid groups. `youtube_describe_server` shows both settings.
- **Tool titles:** every tool has a human-readable `title`.
- **Upload progress:** `youtube_upload_video` sends MCP progress notifications per chunk
  (bytes sent / total) and `youtube_upload_videos` per video.
- The server reports its version in `serverInfo`.
- In-memory end-to-end tests through `mcp.Client`.

### Changed

- **Annotations:** `youtube_set_dry_run` had none; it and the auth/audit tools are now
  annotated as closed-world local tools. `youtube_transition_live_broadcast` and
  `youtube_close_live_chat_poll` are now destructive (ending a broadcast or closing a poll
  can't be undone).
- `youtube_upload_video` and `youtube_upload_videos` are async and run the upload in a
  worker thread. Results, dry-run, the audit log and `YOUTUBE_UPLOAD_DIR` are unchanged.
- Configuration errors (such as an unknown tool group) are shown as a one-line CLI error.

### Deprecated

- The `sse` transport (HTTP+SSE), which the MCP specification deprecates. It still works
  but logs a warning; use `streamable-http`. The default bind stays `127.0.0.1`.

## 0.2.0 (unreleased): AI Shopping Feeds fork

Rebuilt on the official MCP Python SDK 2.3 (`MCPServer`) as an installable package
(`youtube-studio-mcp-server` on PyPI, `youtube-studio-mcp` command).

### Changed

- **MCP SDK 2:** requires `mcp>=2.3.0,<3`. Expected tool errors (refusals, bad
  arguments, YouTube API and quota errors, config problems) are re-raised as
  `ToolError` so clients still see their message; SDK 2 hides other exception text.

### Added

- **Video uploads:** `youtube_upload_video` and `youtube_upload_videos` (bulk) with
  resumable, chunked uploads that resume after network errors, from a local path or URL.
  Optional thumbnail, playlists, scheduling, AI-content and paid-placement flags.
  `youtube_get_upload_status` tracks processing.
- **Full YouTube Data API v3 coverage:** channels, channel sections, banners, watermarks,
  activities, subscriptions, videos (list, update, rate, delete, report, batch stats,
  trainability), playlists, playlist items and images, comments and moderation, captions
  (upload, update, download, delete), search, memberships, Super Chat events,
  third-party links, abuse reports, i18n and categories.
- **Live Streaming API:** broadcasts, streams, cuepoints, live chat, moderators and bans.
- **YouTube Analytics API v2:** any report via `youtube_analytics_query`, plus groups.
- **YouTube Reporting API v1:** report types, jobs, reports and CSV downloads.
- `youtube_call_api` for any method without a dedicated tool.
- Safety: tool annotations, `confirm=true` on deletes, an append-only audit log, dry-run,
  `YOUTUBE_UPLOAD_DIR`, uploads private by default.
- `youtube-studio-mcp auth-init` (Google's installed-app flow), CI, offline tests and an
  agent setup skill in `skills/youtube-studio-mcp`.

### Changed

- Fixed stdio framing: upstream used `Content-Length` headers, which standard MCP clients
  don't send; FastMCP uses newline-delimited JSON-RPC.
- Thumbnails upload with the resumable protocol instead of loading the file into memory.

### Kept

- Upstream tool names (`youtube_channel_overview`, `youtube_list_videos`,
  `youtube_update_video`, `youtube_upload_thumbnail`, ...) and the `YOUTUBE_CLIENT_SECRETS`
  and `YOUTUBE_TOKEN_FILE` variables. Token files from the upstream `scripts/auth.py`
  still load.

### Removed

- `scripts/server.py`, `scripts/auth.py`, `scripts/publish_github.sh` and the demo image.
