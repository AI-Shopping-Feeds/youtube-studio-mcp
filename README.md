<!-- mcp-name: io.github.AI-Shopping-Feeds/youtube-studio-mcp -->

# YouTube MCP Server: YouTube Studio MCP (upload + manage + analytics)

[![CI](https://github.com/AI-Shopping-Feeds/youtube-studio-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/AI-Shopping-Feeds/youtube-studio-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)

This repo contains the source code for an [MCP](https://modelcontextprotocol.io) server
that manages a YouTube channel through the
[YouTube Data API v3](https://developers.google.com/youtube/v3),
[YouTube Analytics API](https://developers.google.com/youtube/analytics) and
[YouTube Reporting API](https://developers.google.com/youtube/reporting). Use it from
Claude, ChatGPT, Cursor, Codex or any MCP client to upload videos in bulk, rewrite titles,
descriptions and tags, and report on channel performance.

This is a fork of [i1s-abhishek/youtube-studio-mcp](https://github.com/i1s-abhishek/youtube-studio-mcp),
maintained by [AI Shopping Feeds](https://github.com/AI-Shopping-Feeds). The upstream server
reads analytics and edits metadata. This fork:

- adds **video uploads**, single and **bulk**, with resumable chunked uploads (up to 256 GB,
  resumes after network errors) from a local path or a URL, plus thumbnail, playlists,
  scheduling and AI-content flags in the same call,
- covers **the whole YouTube Data API v3**: channels, sections, banners, watermarks,
  playlists and cover images, comments and moderation, captions, search, subscriptions,
  memberships, Super Chat, third-party links and more,
- adds the **Live Streaming API**: broadcasts, streams, ad cuepoints, live chat,
  moderators and bans,
- adds any **YouTube Analytics** report and the **Reporting API** bulk CSVs,
- exposes **every other method** through a generic `youtube_call_api` tool,
- adds safety: read/write/destructive tool annotations, `confirm=true` on deletes, an
  audit log, dry-run, private-by-default uploads and an upload-folder allowlist,
- runs on the official MCP Python SDK, so it works with standard MCP clients over stdio.

It pairs with our [Google Ads MCP](https://github.com/AI-Shopping-Feeds/google-ads-mcp)
(turn uploaded videos into video ads) and
[Google Merchant Centre MCP](https://github.com/AI-Shopping-Feeds/google-merchant-centre-mcp).

> **Using an AI agent?** See [Let your agent set it up](#let-your-agent-set-it-up).

## Let your agent set it up

Paste this into Claude Code, Codex, Cursor or any agent that can read web pages and edit files:

```text
Set up the YouTube Studio MCP server for me by following https://raw.githubusercontent.com/AI-Shopping-Feeds/youtube-studio-mcp/main/skills/youtube-studio-mcp/SKILL.md
```

The agent:
- checks whether it's already connected
- installs the runner if you agree
- walks you through the Google Cloud project, OAuth client and sign-in
- adds the server to your client's config without touching your other servers
- checks it works by calling `youtube_channel_overview`

The same file is an [Agent Skill](https://agentskills.io), so your agent can keep it as a guide to using the tools well. For Claude Code, copy the folder into your skills:

```bash
git clone --depth 1 https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git /tmp/youtube-studio-mcp
cp -r /tmp/youtube-studio-mcp/skills/youtube-studio-mcp ~/.claude/skills/
```

Other agents that support skills load the same `skills/youtube-studio-mcp` folder from their own skills directory.

## Tools

107 tools, all prefixed `youtube_`. The full list is in [docs/tools.md](docs/tools.md).

| Area | Tools |
|---|---|
| Uploads | `upload_video`, `upload_videos` (bulk), `get_upload_status`, `upload_thumbnail`, `upload_caption`, `set_playlist_image`, `upload_channel_banner`, `set_watermark` |
| Videos | `list_videos` (your uploads), `get_video`, `videos_list`, `update_video`, `update_video_resource`, `delete_video`, `rate_video`, `batch_get_video_stats`, `get_video_trainability`, `report_video_abuse` |
| Channel | `channel_overview`, `list_channels`, `update_channel`, channel sections, `list_activities`, subscriptions |
| Playlists | `list_playlists`, `create_playlist`, `update_playlist`, `delete_playlist`, `list_playlist_items`, `add_to_playlist`, `update_playlist_item`, `remove_playlist_item` |
| Comments | `list_comments`, `list_comment_replies`, `post_comment`, `reply_to_comment`, `update_comment`, `set_comment_moderation_status`, `mark_comments_as_spam`, `delete_comment` |
| Captions | `list_captions`, `upload_caption`, `update_caption`, `download_caption`, `delete_caption` |
| Discovery | `search`, `list_video_categories`, `list_languages`, `list_regions` |
| Members & links | `list_members`, `list_membership_levels`, `list_super_chat_events`, third-party (store) links, `report_abuse` |
| Live | broadcasts, streams, `bind_live_broadcast`, `transition_live_broadcast`, `insert_cuepoint`, live chat messages, moderators and bans |
| Analytics | `channel_analytics`, `video_analytics`, `analytics_query` (any report), Analytics groups |
| Bulk reports | `list_report_types`, `create_reporting_job`, `list_reporting_jobs`, `list_reports`, `download_report` |
| Server | `auth_status`, `describe_server`, `set_dry_run`, `audit_tail`, `audit_lookup`, `call_api` (any method) |

### Write safety

- Uploads are **private** unless you pass `privacy_status`. Scheduled uploads
  (`publish_at`) stay private until their time.
- Deletes require `confirm=true`, and every tool carries MCP read-only/destructive hints
  so clients can ask before running it.
- Every write and upload is recorded in an append-only audit log (`logs/audit.jsonl`).
- `YOUTUBE_DRY_RUN=true` (or `youtube_set_dry_run`) logs writes without sending them.
- `YOUTUBE_UPLOAD_DIR` limits local uploads to one folder.
- Media is always passed as a path or URL, never as bytes in tool arguments.

### Quota

YouTube Data API quota is per Google Cloud project. `videos.insert` (uploads) and
`search.list` each have their own daily bucket, 100 calls a day by default. Everything else
shares 10,000 units a day: most reads cost 1 unit, most writes 50. Bulk uploads stop at the
first quota error and report which videos were skipped. Request more with Google's
[quota extension form](https://support.google.com/youtube/contact/yt_api_form).

Google has locked uploads from unaudited API projects to private since 2020, but its
current [`videos.insert` reference](https://developers.google.com/youtube/v3/docs/videos/insert)
says they are no longer restricted. Check the privacy of your first upload; if it's
locked, apply for the API compliance audit with the same form.

## Setup instructions

### 1. Google Cloud

Create a project, enable **YouTube Data API v3**, **YouTube Analytics API** and (for bulk
reports) **YouTube Reporting API**, and create an OAuth client of type **Desktop app**.
Step-by-step: [docs/setup-google-oauth.md](docs/setup-google-oauth.md).

### 2. Sign in

```bash
uvx --from git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git \
  youtube-studio-mcp auth-init --client-secrets /abs/path/client_secret.json --output /abs/path/token.json
```

Sign in with the Google account that owns or manages the channel. Add
`--extra-scope memberships` for the memberships tools.

### 3. Configure your MCP client

**Claude Code**

```bash
claude mcp add --scope user youtube \
  --env YOUTUBE_CLIENT_SECRETS=/abs/path/client_secret.json \
  --env YOUTUBE_TOKEN_FILE=/abs/path/token.json \
  -- uvx --from git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git youtube-studio-mcp
```

**Claude Desktop, Cursor, VS Code and other clients**

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

Codex config, every environment variable and HTTP transports:
[docs/mcp-client-config.md](docs/mcp-client-config.md).

## Try it out

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

## Notes

- Upgrading from upstream: tool names, `YOUTUBE_CLIENT_SECRETS`, `YOUTUBE_TOKEN_FILE` and
  token files made by the old `scripts/auth.py` all keep working. The server is now started
  with the `youtube-studio-mcp` command instead of `python3 scripts/server.py`.
- Content-owner (YouTube CMS) accounts can pass `onBehalfOfContentOwner` through the
  `extra_params` argument or `youtube_call_api`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
Changes are listed in [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE). Original work © Abhishek Pandey; fork changes © AI Shopping Feeds.
