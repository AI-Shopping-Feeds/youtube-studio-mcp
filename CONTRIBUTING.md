# Contributing

Thanks for helping improve YouTube Studio MCP.

## Development setup

```bash
git clone https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git
cd youtube-studio-mcp
uv venv && uv pip install -e ".[test,dev]"
```

To try it against a real channel, create an OAuth Desktop client (see
[docs/setup-google-oauth.md](docs/setup-google-oauth.md)) and run
`.venv/bin/youtube-studio-mcp auth-init --client-secrets secrets/client_secret.json`.

## Checks

```bash
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/mypy src/youtube_studio_mcp
.venv/bin/pytest
```

Tests run offline: HTTP is mocked with `respx`. They never touch a real channel.

## Pull requests

- Keep secrets, tokens and channel data out of commits.
- New tools go in the matching module under `src/youtube_studio_mcp/tools/`, use the
  `youtube_` prefix, set read/write/destructive annotations, and require `confirm=true`
  for deletes.
- Media arguments take a local path or URL, never file bytes.
- Update `docs/tools.md` (`youtube-studio-mcp tools`) and the README when tools,
  scopes or setup change.
