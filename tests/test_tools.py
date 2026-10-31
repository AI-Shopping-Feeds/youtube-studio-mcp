from __future__ import annotations

import json

import httpx
import respx

DATA = "https://youtube.googleapis.com/youtube/v3"


@respx.mock
def test_update_video_keeps_unchanged_fields_and_strips_read_only(call):
    respx.get(f"{DATA}/videos").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "V1",
                        "snippet": {
                            "title": "Old",
                            "description": "Keep me",
                            "tags": ["a"],
                            "categoryId": "22",
                            "thumbnails": {},
                            "channelId": "UC1",
                            "publishedAt": "x",
                        },
                        "status": {
                            "privacyStatus": "private",
                            "uploadStatus": "processed",
                            "madeForKids": False,
                            "selfDeclaredMadeForKids": False,
                        },
                    }
                ]
            },
        )
    )
    put = respx.put(f"{DATA}/videos").mock(return_value=httpx.Response(200, json={"id": "V1"}))
    call("youtube_update_video", video_id="V1", title="New", privacy_status="unlisted")
    body = json.loads(put.calls[0].request.content)
    assert body["snippet"] == {
        "title": "New",
        "description": "Keep me",
        "tags": ["a"],
        "categoryId": "22",
    }
    assert body["status"] == {"privacyStatus": "unlisted", "selfDeclaredMadeForKids": False}


@respx.mock
def test_add_to_playlist_inserts_each_video(call):
    route = respx.post(f"{DATA}/playlistItems").mock(
        return_value=httpx.Response(200, json={"id": "PI"})
    )
    result = call("youtube_add_to_playlist", playlist_id="PL1", video_ids=["a", "b"], position=0)
    assert result["added"] == 2
    positions = [json.loads(c.request.content)["snippet"]["position"] for c in route.calls]
    assert positions == [0, 1]


@respx.mock
def test_analytics_query_targets_analytics_api(call):
    route = respx.get("https://youtubeanalytics.googleapis.com/v2/reports").mock(
        return_value=httpx.Response(200, json={"rows": []})
    )
    call(
        "youtube_analytics_query",
        start_date="2026-01-01",
        end_date="2026-01-31",
        dimensions="video",
        sort="-views",
        max_results=5,
    )
    params = route.calls[0].request.url.params
    assert params["ids"] == "channel==MINE"
    assert params["dimensions"] == "video" and params["maxResults"] == "5"


@respx.mock
def test_call_api_writes_are_audited(call):
    respx.post(f"{DATA}/liveBroadcasts/transition").mock(
        return_value=httpx.Response(200, json={"id": "B"})
    )
    result = call(
        "youtube_call_api",
        http_method="POST",
        path="liveBroadcasts/transition",
        params={"id": "B", "broadcastStatus": "live", "part": "status"},
    )
    assert result["_audit_id"]


def test_call_api_rejects_absolute_urls(call):
    try:
        call("youtube_call_api", http_method="GET", path="https://evil.example/x")
    except Exception as e:
        assert "relative" in str(e)
    else:
        raise AssertionError("absolute URL should be rejected")


@respx.mock
def test_api_error_includes_reason(call):
    respx.get(f"{DATA}/search").mock(
        return_value=httpx.Response(
            403, json={"error": {"code": 403, "errors": [{"reason": "quotaExceeded"}]}}
        )
    )
    try:
        call("youtube_search", q="shoes")
    except Exception as e:
        assert "quotaExceeded" in str(e)
    else:
        raise AssertionError("expected quota error")
