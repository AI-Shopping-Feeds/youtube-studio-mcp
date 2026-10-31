"""End-to-end tests through a real MCP client connected in-memory (mcp.Client)."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import httpx
import pytest
import respx
from mcp import Client

from youtube_studio_mcp.config import Config, load_config
from youtube_studio_mcp.server import build_server
from youtube_studio_mcp.tools import GROUPS

from .conftest import FakeAuth

pytestmark = pytest.mark.anyio

DATA = "https://youtube.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
SESSION = "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=xyz"
CHUNK = 256 * 1024
ALWAYS = {
    "youtube_auth_status",
    "youtube_describe_server",
    "youtube_audit_tail",
    "youtube_audit_lookup",
    "youtube_set_dry_run",
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def _tools(config: Config) -> list[Any]:
    async with Client(build_server(config=config, auth=FakeAuth())) as client:
        return (await client.list_tools()).tools


def _json(result: Any) -> Any:
    return json.loads(result.content[0].text)


async def test_every_tool_has_title_and_annotations(config):
    tools = await _tools(config)
    assert len(tools) == 107
    for tool in tools:
        assert tool.title, f"{tool.name} has no title"
        assert tool.title[0].isupper() and not tool.title.endswith(".")
        assert tool.annotations is not None, f"{tool.name} has no annotations"
        assert tool.annotations.read_only_hint is not None, tool.name
        if not tool.annotations.read_only_hint:
            assert tool.annotations.destructive_hint is not None, tool.name


async def test_annotation_classification(config):
    tools = {t.name: t.annotations for t in await _tools(config)}
    assert tools["youtube_set_dry_run"].read_only_hint is False
    assert tools["youtube_set_dry_run"].open_world_hint is False
    for name in ("youtube_delete_video", "youtube_call_api", "youtube_transition_live_broadcast"):
        assert tools[name].destructive_hint is True, name
    # Every tool that takes confirm=true is annotated destructive.
    for name, ann in tools.items():
        if "delete" in name or name.startswith("youtube_remove_"):
            assert ann.destructive_hint is True, name


async def test_tools_list_order_is_deterministic(config):
    first = [t.name for t in await _tools(config)]
    second = [t.name for t in await _tools(config)]
    assert first == second
    assert first[: len(ALWAYS)] == [
        "youtube_auth_status",
        "youtube_describe_server",
        "youtube_audit_tail",
        "youtube_audit_lookup",
        "youtube_set_dry_run",
    ]


async def test_server_reports_version(config):
    from youtube_studio_mcp import __version__

    async with Client(build_server(config=config, auth=FakeAuth())) as client:
        assert client.server_info is not None
        assert client.server_info.name == "youtube-studio-mcp"
        assert client.server_info.version == __version__


async def test_tool_groups_filter(config):
    names = {t.name for t in await _tools(replace(config, tool_groups=("uploads", "captions")))}
    assert names >= ALWAYS
    assert "youtube_upload_video" in names and "youtube_list_captions" in names
    assert "youtube_list_videos" not in names and "youtube_call_api" not in names
    assert len(names) == len(ALWAYS) + 3 + 5


async def test_read_only_filter(config):
    everything = await _tools(config)
    tools = await _tools(replace(config, read_only=True))
    names = {t.name for t in tools}
    assert names >= ALWAYS  # youtube_set_dry_run stays even though it isn't read-only
    for tool in tools:
        if tool.name not in ALWAYS:
            assert tool.annotations.read_only_hint is True, tool.name
    expected = {t.name for t in everything if t.annotations.read_only_hint} | ALWAYS
    assert names == expected


async def test_read_only_combines_with_groups(config):
    names = {t.name for t in await _tools(replace(config, tool_groups=("videos",), read_only=True))}
    assert "youtube_get_video" in names
    assert "youtube_update_video" not in names and "youtube_delete_video" not in names


def test_unknown_group_fails_at_startup(config, monkeypatch, tmp_path):
    with pytest.raises(RuntimeError, match="Valid groups: channels, videos, uploads"):
        build_server(config=replace(config, tool_groups=("videos", "bogus")), auth=FakeAuth())

    monkeypatch.setenv("YOUTUBE_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    monkeypatch.setenv("YOUTUBE_TOOL_GROUPS", " Videos , bogus,")
    with pytest.raises(RuntimeError) as err:
        load_config()
    assert "bogus" in str(err.value)
    for group in GROUPS:
        assert group in str(err.value)

    monkeypatch.setenv("YOUTUBE_TOOL_GROUPS", " Videos , uploads,videos")
    monkeypatch.setenv("YOUTUBE_READ_ONLY", "true")
    loaded = load_config()
    assert loaded.tool_groups == ("videos", "uploads")
    assert loaded.read_only is True


@respx.mock
async def test_read_tool_returns_result(config):
    route = respx.get(f"{DATA}/videos").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "V1", "snippet": {"title": "Hello"}}]}
        )
    )
    async with Client(build_server(config=config, auth=FakeAuth())) as client:
        result = await client.call_tool("youtube_get_video", {"video_id": "V1"})
    assert not result.is_error
    assert _json(result) == {"id": "V1", "snippet": {"title": "Hello"}}
    assert route.calls[0].request.url.params["id"] == "V1"


async def test_delete_without_confirm_reaches_client(config):
    with respx.mock(assert_all_called=False) as mock:
        async with Client(build_server(config=config, auth=FakeAuth())) as client:
            result = await client.call_tool("youtube_delete_video", {"video_id": "V1"})
        assert not mock.calls
    assert result.is_error
    assert "confirm=true" in result.content[0].text


async def test_upload_sends_progress_notifications(config, tmp_path):
    path = tmp_path / "clip.mp4"
    size = CHUNK * 3 + 10
    path.write_bytes(b"\0" * size)
    updates: list[tuple[float, float | None, str | None]] = []

    async def on_progress(progress: float, total: float | None, message: str | None) -> None:
        updates.append((progress, total, message))

    def chunk(request: httpx.Request) -> httpx.Response:
        end = int(request.headers["Content-Range"].split()[1].split("/")[0].split("-")[1])
        if end + 1 < size:
            return httpx.Response(308, headers={"Range": f"bytes=0-{end}"})
        return httpx.Response(200, json={"id": "VIDP"})

    with respx.mock:
        respx.post(UPLOAD).mock(return_value=httpx.Response(200, headers={"Location": SESSION}))
        respx.put(SESSION).mock(side_effect=chunk)
        async with Client(build_server(config=config, auth=FakeAuth())) as client:
            result = await client.call_tool(
                "youtube_upload_video",
                {"source": str(path), "title": "Progress"},
                progress_callback=on_progress,
            )

    assert not result.is_error, result.content
    assert _json(result)["video_id"] == "VIDP"
    assert [p for p, _, _ in updates] == [CHUNK, 2 * CHUNK, 3 * CHUNK, size]
    assert all(total == size for _, total, _ in updates)
    assert updates[-1][2] == f"Uploaded {size:,} of {size:,} bytes"


async def test_bulk_upload_reports_progress_per_video(config, tmp_path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"\0" * 10)
    updates: list[tuple[float, float | None]] = []

    async def on_progress(progress: float, total: float | None, message: str | None) -> None:
        updates.append((progress, total))

    videos = [
        {"source": str(path), "title": "a"},
        {"source": str(tmp_path / "missing.mp4"), "title": "b"},
        {"source": str(path), "title": "c"},
    ]
    with respx.mock:
        respx.post(UPLOAD).mock(return_value=httpx.Response(200, headers={"Location": SESSION}))
        respx.put(SESSION).mock(return_value=httpx.Response(200, json={"id": "B1"}))
        async with Client(build_server(config=config, auth=FakeAuth())) as client:
            result = await client.call_tool(
                "youtube_upload_videos", {"videos": videos}, progress_callback=on_progress
            )

    body = _json(result)
    assert body["uploaded"] == 2 and body["failed"] == 1
    assert updates == [(1, 3), (2, 3), (3, 3)]


async def test_dry_run_upload_through_client_sends_nothing(config, tmp_path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"\0" * 10)
    with respx.mock(assert_all_called=False) as mock:
        async with Client(build_server(config=config, auth=FakeAuth())) as client:
            await client.call_tool("youtube_set_dry_run", {"enabled": True})
            result = await client.call_tool(
                "youtube_upload_video",
                {"source": str(path), "title": "t", "privacy_status": "public"},
            )
        assert not mock.calls
    video = _json(result)["video"]
    assert video["_dry_run"] is True
    assert video["body"]["status"]["privacyStatus"] == "public"
