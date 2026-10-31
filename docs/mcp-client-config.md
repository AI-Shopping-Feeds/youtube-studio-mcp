# MCP client configuration

The server runs locally over stdio. The examples use `uvx` from [uv](https://docs.astral.sh/uv/);
`pipx run --spec git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git youtube-studio-mcp` works too.

## Claude Code

```bash
claude mcp add --scope user youtube \
  --env YOUTUBE_CLIENT_SECRETS=/abs/path/client_secret.json \
  --env YOUTUBE_TOKEN_FILE=/abs/path/token.json \
  -- uvx --from git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git youtube-studio-mcp
```

## Claude Desktop, Cursor and other JSON configs

```json
"youtube": {
  "command": "/full/path/to/uvx",
  "args": ["--from", "git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git", "youtube-studio-mcp"],
  "env": {
    "YOUTUBE_CLIENT_SECRETS": "/abs/path/client_secret.json",
    "YOUTUBE_TOKEN_FILE": "/abs/path/token.json"
  }
}
```

Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows). Cursor: `~/.cursor/mcp.json`.

## Codex

```toml
[mcp_servers.youtube]
command = "uvx"
args = ["--from", "git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git", "youtube-studio-mcp"]
env = { YOUTUBE_CLIENT_SECRETS = "/abs/path/client_secret.json", YOUTUBE_TOKEN_FILE = "/abs/path/token.json" }
```

The repo also ships `.codex-plugin/plugin.json` and `.mcp.json` for use as a Codex plugin.

## Running over HTTP (streamable-http)

stdio is the simplest setup for a single local client. To serve the tools over HTTP, use the
`streamable-http` transport, which is the current MCP standard:

```bash
youtube-studio-mcp --transport streamable-http --port 8000
# Claude Code:
claude mcp add --transport http youtube http://127.0.0.1:8000/mcp
```

The server binds to `127.0.0.1` by default and has no authentication of its own, so keep it
on localhost or put it behind an authenticating proxy before setting `YOUTUBE_HOST=0.0.0.0`.

The `sse` transport (HTTP+SSE) still works for older clients but is deprecated by the MCP
specification; the server logs a warning when it is used. Prefer `streamable-http`.

## Limiting the tool list

Large tool lists cost context and make tool choice harder. Expose only what you need:

- `YOUTUBE_TOOL_GROUPS=videos,uploads,analytics` registers only those tool groups. Groups:
  `channels`, `videos`, `uploads`, `playlists`, `comments`, `captions`, `search`, `live`,
  `analytics`, `raw`. An unknown group stops the server at startup with the list of valid
  groups.
- `YOUTUBE_READ_ONLY=true` registers only read-only tools, for reporting or research
  agents that must not change the channel.

The auth, server, audit and dry-run tools are always registered.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `YOUTUBE_CLIENT_SECRETS` | `secrets/client_secret.json` | OAuth Desktop client JSON |
| `YOUTUBE_TOKEN_FILE` | `secrets/token.json` | Token saved by `auth-init` |
| `YOUTUBE_UPLOAD_DIR` | unset | Only allow local uploads from this folder |
| `YOUTUBE_DRY_RUN` | `false` | Log writes and uploads without sending them |
| `YOUTUBE_AUDIT_LOG` | `logs/audit.jsonl` | Where writes are recorded |
| `YOUTUBE_UPLOAD_CHUNK_MB` | `8` | Resumable upload chunk size |
| `YOUTUBE_TIMEOUT` | `60` | HTTP timeout in seconds |
| `YOUTUBE_LOG_LEVEL` | `INFO` | Log level (logs go to stderr) |
| `YOUTUBE_TOOL_GROUPS` | unset (all) | Comma-separated tool groups to register |
| `YOUTUBE_READ_ONLY` | `false` | Register only read-only tools |
| `YOUTUBE_TRANSPORT` | `stdio` | `stdio`, `streamable-http` (recommended for HTTP) or `sse` (deprecated) |
| `YOUTUBE_HOST` | `127.0.0.1` | Bind host for HTTP transports |
| `YOUTUBE_PORT` | `8000` | Bind port for HTTP transports |
