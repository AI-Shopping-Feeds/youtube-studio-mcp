"""Shared fixtures. Tests run offline: HTTP is mocked with respx and auth is faked."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from youtube_studio_mcp import client as client_module
from youtube_studio_mcp.config import Config
from youtube_studio_mcp.server import build_server


class FakeAuth:
    account_label = "fake:test"

    def access_token(self) -> str:
        return "fake-token"

    def status(self) -> dict[str, Any]:
        return {"token_exists": True}


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_module.time, "sleep", lambda _s: None)


@pytest.fixture
def config(tmp_path: Path) -> Config:
    return Config(
        client_secrets=tmp_path / "client_secret.json",
        token_file=tmp_path / "token.json",
        audit_log=tmp_path / "audit.jsonl",
        upload_chunk_size=256 * 1024,
        timeout=5.0,
    )


@pytest.fixture
def server(config: Config):
    return build_server(config=config, auth=FakeAuth())


@pytest.fixture
def call(server):
    """Call a tool by name and return its parsed JSON result."""

    def _call(name: str, **args: Any) -> Any:
        result = asyncio.run(server.call_tool(name, args))
        return json.loads(result.content[0].text)

    return _call
