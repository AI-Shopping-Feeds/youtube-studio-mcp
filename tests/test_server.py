from __future__ import annotations

import asyncio

from youtube_studio_mcp.client import clean_params

LEGACY_TOOLS = {
    "youtube_auth_status",
    "youtube_channel_overview",
    "youtube_list_videos",
    "youtube_get_video",
    "youtube_update_video",
    "youtube_upload_thumbnail",
    "youtube_channel_analytics",
    "youtube_video_analytics",
    "youtube_post_comment",
    "youtube_list_comments",
}


def test_tools_register_with_unique_names(server):
    tools = asyncio.run(server.list_tools())
    names = [t.name for t in tools]
    assert len(names) == len(set(names))
    assert len(names) >= 100
    assert set(names) >= LEGACY_TOOLS, "upstream tool names must keep working"
    assert all(n.startswith("youtube_") for n in names)
    assert all(t.description for t in tools)


def test_read_only_and_destructive_annotations(server):
    tools = {t.name: t for t in asyncio.run(server.list_tools())}
    assert tools["youtube_list_videos"].annotations.read_only_hint is True
    assert tools["youtube_delete_video"].annotations.destructive_hint is True
    assert tools["youtube_upload_video"].annotations.read_only_hint is False


def test_clean_params():
    assert clean_params({"a": None, "b": True, "c": ["x", "y"], "d": 3}) == {
        "b": "true",
        "c": "x,y",
        "d": 3,
    }


def test_delete_requires_confirm(call):
    try:
        call("youtube_delete_video", video_id="abc")
    except Exception as e:
        assert "confirm=true" in str(e)
    else:
        raise AssertionError("delete without confirm should fail")
