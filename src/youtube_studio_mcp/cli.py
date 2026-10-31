"""`youtube-studio-mcp` console script.

* `youtube-studio-mcp` / `youtube-studio-mcp run` — start the MCP server.
* `youtube-studio-mcp auth-init` — sign in with Google and save a token file.
* `youtube-studio-mcp tools` — list the registered tools.
* `youtube-studio-mcp version`.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import click

from . import __version__
from .auth import OPTIONAL_SCOPES, SCOPES
from .config import load_config


@click.group(invoke_without_command=True)
@click.option(
    "--env",
    "env_file",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to a .env file (default ./.env).",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default=None,
    help="Override YOUTUBE_TRANSPORT.",
)
@click.option("--host", default=None, help="Bind host for HTTP transports.")
@click.option("--port", type=int, default=None, help="Bind port for HTTP transports.")
@click.pass_context
def cli(
    ctx: click.Context,
    env_file: Path | None,
    transport: str | None,
    host: str | None,
    port: int | None,
) -> None:
    """YouTube Studio MCP server."""
    ctx.ensure_object(dict)
    ctx.obj.update(env_file=env_file, transport=transport, host=host, port=port)
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command()
@click.pass_context
def run(ctx: click.Context) -> None:
    """Start the MCP server (default)."""
    from .server import build_server

    config = load_config(env_file=ctx.obj.get("env_file"))
    config.transport = ctx.obj.get("transport") or config.transport
    config.host = ctx.obj.get("host") or config.host
    config.port = ctx.obj.get("port") or config.port
    mcp = build_server(config=config)
    if config.transport != "stdio":
        mcp.settings.host = config.host
        mcp.settings.port = config.port
    mcp.run(config.transport)  # type: ignore[arg-type]


@cli.command("auth-init")
@click.option(
    "--client-secrets",
    "secrets_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="OAuth Desktop client JSON from Google Cloud (default YOUTUBE_CLIENT_SECRETS).",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Where to save the token (default YOUTUBE_TOKEN_FILE).",
)
@click.option(
    "--extra-scope",
    "extra",
    multiple=True,
    type=click.Choice(sorted(OPTIONAL_SCOPES)),
    help="Also request an optional scope (memberships, partner, partner-channel-audit).",
)
@click.option("--port", type=int, default=0, help="Local OAuth callback port (0 = any free port).")
@click.pass_context
def auth_init(
    ctx: click.Context,
    secrets_path: Path | None,
    output_path: Path | None,
    extra: tuple[str, ...],
    port: int,
) -> None:
    """Sign in with Google in the browser and save a refresh token."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    config = load_config(env_file=ctx.obj.get("env_file"))
    secrets_path = secrets_path or config.client_secrets
    output_path = output_path or config.token_file
    if not secrets_path.exists():
        raise click.ClickException(f"Client secrets file not found: {secrets_path}")
    scopes = SCOPES + [OPTIONAL_SCOPES[name] for name in extra]
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), scopes)
    creds = flow.run_local_server(port=port, prompt="consent", access_type="offline")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(creds.to_json(), encoding="utf-8")
    output_path.chmod(0o600)
    click.echo(f"Saved token to {output_path}")
    click.echo(f"Set YOUTUBE_TOKEN_FILE={output_path.resolve()} in your MCP client config.")


@cli.command()
@click.pass_context
def tools(ctx: click.Context) -> None:
    """List every tool the server exposes."""
    from .server import build_server

    mcp = build_server(config=load_config(env_file=ctx.obj.get("env_file")))
    for tool in sorted(asyncio.run(mcp.list_tools()), key=lambda t: t.name):
        click.echo(f"{tool.name}: {(tool.description or '').splitlines()[0]}")


@cli.command()
def version() -> None:
    """Print the package version."""
    click.echo(__version__)


def main() -> None:
    cli(obj={})


if __name__ == "__main__":
    main()
