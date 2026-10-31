# Changelog

## 0.2.0 (unreleased): AI Shopping Feeds fork

Rebuilt on the official MCP Python SDK (FastMCP) as an installable package
(`youtube-studio-mcp-server` on PyPI, `youtube-studio-mcp` command).

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
