<!-- mcp-name: io.github.AI-Shopping-Feeds/youtube-studio-mcp -->

# YouTube Studio MCP Server (read + write)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/) [![Fork of i1s-abhishek/youtube-studio-mcp](https://img.shields.io/badge/fork%20of-i1s--abhishek%2Fyoutube--studio--mcp-lightgrey.svg)](https://github.com/i1s-abhishek/youtube-studio-mcp)

An [MCP](https://modelcontextprotocol.io) server for YouTube channels, using the
[YouTube Data API v3](https://developers.google.com/youtube/v3),
[YouTube Analytics API](https://developers.google.com/youtube/analytics) and
[YouTube Reporting API](https://developers.google.com/youtube/reporting). Use it from
Claude, ChatGPT, Cursor, Codex or any MCP client to upload videos in bulk, rewrite
titles, descriptions and tags, manage playlists, comments, captions and live streams,
and report on channel performance.

This is a fork of [i1s-abhishek/youtube-studio-mcp](https://github.com/i1s-abhishek/youtube-studio-mcp), maintained by [AI Shopping Feeds](https://github.com/AI-Shopping-Feeds). Upstream reads analytics and edits video metadata. This fork adds:

- **video uploads**, single and **bulk**, with resumable uploads from a local path or a URL, plus thumbnails, playlists, scheduling and AI-content flags
- **the whole YouTube Data API v3**: channels, sections, branding, playlists, comments and moderation, captions, search, subscriptions, memberships and more
- the **Live Streaming API**, any **YouTube Analytics** report and **Reporting API** bulk CSVs
- **every other method** through a generic `youtube_call_api` tool
- safety: tool annotations, `confirm=true` on deletes, an audit log, dry-run and private-by-default uploads

Part of the AI Shopping Feeds MCP family: [Google Ads](https://github.com/AI-Shopping-Feeds/google-ads-mcp) · [Google Merchant Centre](https://github.com/AI-Shopping-Feeds/google-merchant-centre-mcp) · [Google Analytics](https://github.com/AI-Shopping-Feeds/google-analytics-mcp) · **YouTube Studio**.

## Let your agent set it up

Paste this into Claude Code, Codex, Cursor or any agent that can read web pages and edit files:

```text
Set up the YouTube Studio MCP server for me by following https://raw.githubusercontent.com/AI-Shopping-Feeds/youtube-studio-mcp/main/skills/youtube-studio-mcp/SKILL.md
```

The agent checks whether it's already connected, installs the runner if you
agree, walks you through the Google Cloud project, OAuth client and sign-in, adds the server to your
client's config without touching your other servers, and checks it works by
calling `youtube_channel_overview`.

The same file is an [Agent Skill](https://agentskills.io), so your agent can keep it as a guide to using the tools well. For Claude Code, copy the folder into your skills:

```bash
git clone --depth 1 https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git /tmp/youtube-studio-mcp
cp -r /tmp/youtube-studio-mcp/skills/youtube-studio-mcp ~/.claude/skills/
```

Other agents that support skills load the same `skills/youtube-studio-mcp` folder from their own skills directory.

## What it can do

107 tools, all prefixed `youtube_`. The full list is in [docs/tools.md](docs/tools.md).

### Read

| Area | Tools |
|---|---|
| Channel | `channel_overview`, `list_channels`, `list_activities`, channel sections, subscriptions |
| Videos | `list_videos`, `get_video`, `videos_list`, `batch_get_video_stats`, `get_video_rating`, `get_upload_status` |
| Playlists and comments | `list_playlists`, `list_playlist_items`, `list_comments`, `list_comment_replies` |
| Captions and discovery | `list_captions`, `download_caption`, `search`, `list_video_categories`, `list_languages`, `list_regions` |
| Members and live | `list_members`, `list_membership_levels`, `list_super_chat_events`, live broadcasts, streams and chat |
| Analytics | `channel_analytics`, `video_analytics`, `analytics_query` (any report), Reporting API jobs and `download_report` |

### Write

| Area | Tools |
|---|---|
| Uploads | `upload_video`, `upload_videos` (bulk), `upload_thumbnail`, `upload_caption`, `upload_channel_banner`, `set_watermark` |
| Videos | `update_video`, `update_video_resource`, `delete_video`, `rate_video` |
| Channel | `update_channel`, channel sections, `subscribe`, `unsubscribe`, third-party links |
| Playlists | `create_playlist`, `update_playlist`, `delete_playlist`, `add_to_playlist`, `update_playlist_item`, `remove_playlist_item`, `set_playlist_image` |
| Comments | `post_comment`, `reply_to_comment`, `update_comment`, `set_comment_moderation_status`, `mark_comments_as_spam`, `delete_comment` |
| Live | create/update/delete broadcasts and streams, `bind_live_broadcast`, `transition_live_broadcast`, `insert_cuepoint`, chat messages, moderators and bans |
| Any method | `call_api` |

### Safety

- Uploads are **private** unless you set `privacy_status`. Scheduled uploads stay private until their time.
- Deletes need `confirm=true`, and every tool carries a title and MCP read-only/destructive hints.
- `YOUTUBE_READ_ONLY=true` hides every tool that can change the channel; `YOUTUBE_TOOL_GROUPS` exposes only the groups you need.
- Every write and upload is recorded in an append-only audit log (`logs/audit.jsonl`).
- Dry-run (`YOUTUBE_DRY_RUN=true` or `youtube_set_dry_run`) logs writes without sending them.
- `YOUTUBE_UPLOAD_DIR` limits local uploads to one folder. Video bytes are never passed as tool arguments.
- YouTube Data API quota is per Google Cloud project: uploads and search have 100 calls a day each by default. See [docs/setup-google-oauth.md](docs/setup-google-oauth.md#quota-and-the-upload-audit).

## Supported clients

| Client | Works? | How |
|---|---|---|
| Claude Code | ✅ | Local server, `claude mcp add` (below) |
| Claude Desktop | ✅ | Local server, `claude_desktop_config.json` |
| Cursor | ✅ | Local server, `~/.cursor/mcp.json` |
| VS Code (Copilot) | ✅ | Local server, `.vscode/mcp.json` (uses `servers` instead of `mcpServers`) |
| Codex | ✅ | Local server, `~/.codex/config.toml` |
| Gemini CLI | ✅ | Local server, `~/.gemini/settings.json` |
| Windsurf and other local clients | ✅ | Local server, same JSON entry |
| Claude.ai and ChatGPT | ❌ not yet | These need a remote server with sign-in. This server's HTTP transports have no sign-in, so don't expose them publicly. Use a local client. |

## Setup

### 1. Install uv

The server runs with `uvx` from [uv](https://docs.astral.sh/uv/getting-started/installation/)
(`brew install uv` on macOS) and needs Python 3.10 or later. It installs straight
from this repository:

```shell
uvx --from git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git youtube-studio-mcp
```

Pin a release by adding `@vX.Y.Z` to the URL.

### 2. Get credentials

1. **Google Cloud:** create a project, enable **YouTube Data API v3**, **YouTube
   Analytics API** and (for bulk reports) **YouTube Reporting API**, and create an
   OAuth client of type **Desktop app**. Step by step:
   [docs/setup-google-oauth.md](docs/setup-google-oauth.md).
2. **Sign in** with the Google account that owns or manages the channel:

   ```shell
   uvx --from git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git \
     youtube-studio-mcp auth-init --client-secrets /abs/path/client_secret.json --output /abs/path/token.json
   ```

   Add `--extra-scope memberships` for the memberships tools.

### 3. Add it to your client

Replace the placeholders. Keep your other servers in each file.

**Claude Code**

```bash
claude mcp add --scope user youtube \
  --env YOUTUBE_CLIENT_SECRETS=/abs/path/client_secret.json \
  --env YOUTUBE_TOKEN_FILE=/abs/path/token.json \
  --env YOUTUBE_UPLOAD_DIR=/abs/path/videos \
  -- uvx --from git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git youtube-studio-mcp
```

**Claude Desktop, Cursor, Gemini CLI, Windsurf** (and VS Code under `servers`)

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git", "youtube-studio-mcp"],
      "env": {
        "YOUTUBE_CLIENT_SECRETS": "/abs/path/client_secret.json",
        "YOUTUBE_TOKEN_FILE": "/abs/path/token.json",
        "YOUTUBE_UPLOAD_DIR": "/abs/path/videos"
      }
    }
  }
}
```

Desktop apps often can't find `uvx` on the PATH; if the server doesn't start, use
the full path from `which uvx` as the `command`.

**Codex** (`~/.codex/config.toml`)

```toml
[mcp_servers.youtube]
command = "uvx"
args = ["--from", "git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git", "youtube-studio-mcp"]
env = { YOUTUBE_CLIENT_SECRETS = "/abs/path/client_secret.json", YOUTUBE_TOKEN_FILE = "/abs/path/token.json", YOUTUBE_UPLOAD_DIR = "/abs/path/videos" }
```

### 4. Check it works

Restart or reload the client, then ask it to "give me an overview of my YouTube channel". It should
call `youtube_channel_overview`.

## Configuration

| Variable | Required | What it does |
|---|---|---|
| `YOUTUBE_CLIENT_SECRETS` | yes | Path to the OAuth client JSON |
| `YOUTUBE_TOKEN_FILE` | yes | Path to the token saved by `auth-init` |
| `YOUTUBE_UPLOAD_DIR` | recommended | Folder that local videos may be uploaded from |
| `YOUTUBE_DRY_RUN` | no | `true` logs writes without sending them |
| `YOUTUBE_AUDIT_LOG` | no | Audit log path (default `logs/audit.jsonl`) |
| `YOUTUBE_UPLOAD_CHUNK_MB` | no | Upload chunk size |
| `YOUTUBE_PAGE_SIZE`, `YOUTUBE_TIMEOUT`, `YOUTUBE_LOG_LEVEL` | no | List page size, request timeout and log level |
| `YOUTUBE_TOOL_GROUPS` | no | Comma-separated tool groups to register (default all): `channels`, `videos`, `uploads`, `playlists`, `comments`, `captions`, `search`, `live`, `analytics`, `raw`. Auth, server, audit and dry-run tools are always on |
| `YOUTUBE_READ_ONLY` | no | `true` registers only read-only tools |
| `YOUTUBE_TRANSPORT`, `YOUTUBE_HOST`, `YOUTUBE_PORT` | no | `stdio` (default), `streamable-http` (recommended for HTTP) or `sse` (deprecated by the MCP spec; logs a warning), and its bind address (default `127.0.0.1:8000`) |

## Example prompts

```text
Upload every .mp4 in /Users/me/videos/ads as unlisted, with titles from the file names, and add them to my "Product ads" playlist.
```

```text
Show my top 10 videos by views for the last 28 days and suggest better titles and tags for the bottom 3.
```

```text
Download the English captions for VIDEO_ID as SRT and upload a Spanish translation.
```

```text
Hold every comment mentioning "giveaway" for review on my last 5 videos.
```

## More docs

- [All tools](docs/tools.md)
- [Google OAuth setup, scopes and quota](docs/setup-google-oauth.md)
- [MCP client configuration and every environment variable](docs/mcp-client-config.md)
- [Agent skill](skills/youtube-studio-mcp/SKILL.md): setup and usage guide for agents
- [Changelog](CHANGELOG.md) and [security policy](SECURITY.md)

## Contributing and licence

Issues and pull requests are welcome on [this repository](https://github.com/AI-Shopping-Feeds/youtube-studio-mcp). See
[CONTRIBUTING.md](CONTRIBUTING.md).

Licensed under the [MIT License](LICENSE). Based on [i1s-abhishek/youtube-studio-mcp](https://github.com/i1s-abhishek/youtube-studio-mcp) by Abhishek Pandey.

- Upgrading from upstream: tool names, `YOUTUBE_CLIENT_SECRETS`, `YOUTUBE_TOKEN_FILE` and old token files keep working. Start the server with the `youtube-studio-mcp` command instead of `python3 scripts/server.py`.
- Content-owner (YouTube CMS) accounts can pass `onBehalfOfContentOwner` through `extra_params` or `youtube_call_api`.

---

Try out [AI Shopping Feeds](https://aishoppingfeeds.com/), our shopping feed management tool (including Google Shopping feeds).
