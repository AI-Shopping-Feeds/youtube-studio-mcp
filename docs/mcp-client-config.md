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
| `YOUTUBE_TRANSPORT` | `stdio` | `stdio`, `sse` or `streamable-http` |
