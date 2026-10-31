from __future__ import annotations

import json

import httpx
import respx

UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
SESSION = "https://www.googleapis.com/upload/youtube/v3/videos?upload_id=xyz"
CHUNK = 256 * 1024


def _video_file(tmp_path, size=CHUNK * 2 + 10):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"\0" * size)
    return path


@respx.mock
def test_resumable_upload_sends_chunks_and_metadata(call, tmp_path):
    path = _video_file(tmp_path)
    start = respx.post(UPLOAD).mock(return_value=httpx.Response(200, headers={"Location": SESSION}))
    ranges = []

    def chunk(request):
        ranges.append(request.headers["Content-Range"])
        end = int(request.headers["Content-Range"].split()[1].split("/")[0].split("-")[1])
        if end + 1 < path.stat().st_size:
            return httpx.Response(308, headers={"Range": f"bytes=0-{end}"})
        return httpx.Response(200, json={"id": "VID123", "status": {"privacyStatus": "private"}})

    respx.put(SESSION).mock(side_effect=chunk)

    result = call(
        "youtube_upload_video",
        source=str(path),
        title="Red trainers",
        tags=["shoes"],
        contains_synthetic_media=True,
    )

    assert result["video_id"] == "VID123"
    sent = start.calls[0].request
    assert sent.url.params["uploadType"] == "resumable"
    assert sent.url.params["part"] == "snippet,status"
    assert sent.headers["X-Upload-Content-Length"] == str(path.stat().st_size)
    body = json.loads(sent.content)
    assert body["snippet"]["title"] == "Red trainers"
    assert body["status"]["privacyStatus"] == "private"
    assert body["status"]["containsSyntheticMedia"] is True
    size = path.stat().st_size
    assert ranges == [
        f"bytes 0-{CHUNK - 1}/{size}",
        f"bytes {CHUNK}-{2 * CHUNK - 1}/{size}",
        f"bytes {2 * CHUNK}-{size - 1}/{size}",
    ]


@respx.mock
def test_upload_resumes_after_server_error(call, tmp_path):
    path = _video_file(tmp_path, size=CHUNK + 5)
    respx.post(UPLOAD).mock(return_value=httpx.Response(200, headers={"Location": SESSION}))
    seen = []

    def chunk(request):
        rng = request.headers["Content-Range"]
        seen.append(rng)
        if rng == f"bytes */{CHUNK + 5}":  # status query after the failure
            return httpx.Response(308, headers={"Range": f"bytes=0-{CHUNK - 1}"})
        if rng.startswith("bytes 0-"):
            return httpx.Response(308, headers={"Range": f"bytes=0-{CHUNK - 1}"})
        if len([s for s in seen if s.startswith(f"bytes {CHUNK}-")]) == 1:
            return httpx.Response(503)
        return httpx.Response(201, json={"id": "VID9"})

    respx.put(SESSION).mock(side_effect=chunk)
    result = call("youtube_upload_video", source=str(path), title="t")
    assert result["video_id"] == "VID9"
    assert f"bytes */{CHUNK + 5}" in seen


@respx.mock
def test_bulk_upload_stops_on_quota(call, tmp_path):
    a = _video_file(tmp_path, size=10)
    respx.post(UPLOAD).mock(
        side_effect=[
            httpx.Response(200, headers={"Location": SESSION}),
            httpx.Response(403, json={"error": {"errors": [{"reason": "quotaExceeded"}]}}),
        ]
    )
    respx.put(SESSION).mock(return_value=httpx.Response(200, json={"id": "A1"}))
    videos = [{"source": str(a), "title": f"v{i}"} for i in range(3)]
    result = call("youtube_upload_videos", videos=videos)
    assert result["uploaded"] == 1
    assert result["failed"] == 1
    assert result["skipped"] == 1
    assert result["video_ids"] == ["A1"]
    assert "quotaExceeded" in result["results"][1]["error"]


@respx.mock
def test_bulk_upload_reports_missing_file_and_continues(call, tmp_path):
    a = _video_file(tmp_path, size=10)
    respx.post(UPLOAD).mock(return_value=httpx.Response(200, headers={"Location": SESSION}))
    respx.put(SESSION).mock(return_value=httpx.Response(200, json={"id": "B2"}))
    result = call(
        "youtube_upload_videos",
        videos=[
            {"source": str(tmp_path / "missing.mp4"), "title": "x"},
            {"source": str(a), "title": "y"},
        ],
    )
    assert result["uploaded"] == 1 and result["failed"] == 1
    assert "File not found" in result["results"][0]["error"]


@respx.mock
def test_upload_from_url_downloads_then_cleans_up(call, tmp_path):
    respx.get("https://cdn.example.com/ad.mp4").mock(
        return_value=httpx.Response(200, content=b"video-bytes")
    )
    respx.post(UPLOAD).mock(return_value=httpx.Response(200, headers={"Location": SESSION}))
    seen_sizes = []

    def chunk(request):
        seen_sizes.append(len(request.content))
        return httpx.Response(200, json={"id": "URL1"})

    respx.put(SESSION).mock(side_effect=chunk)
    result = call("youtube_upload_video", source="https://cdn.example.com/ad.mp4", title="ad")
    assert result["video_id"] == "URL1"
    assert seen_sizes == [len(b"video-bytes")]


def test_dry_run_upload_sends_nothing(call, server, tmp_path):
    path = _video_file(tmp_path, size=10)
    call("youtube_set_dry_run", enabled=True)
    with respx.mock(assert_all_called=False) as mock:
        result = call(
            "youtube_upload_video",
            source=str(path),
            title="t",
            publish_at="2030-01-01T00:00:00Z",
            privacy_status="public",
        )
        assert not mock.calls
    assert result["video"]["_dry_run"] is True
    assert result["video"]["body"]["status"]["privacyStatus"] == "private"
    entries = call("youtube_audit_tail")["entries"]
    assert entries[-1]["dry_run"] is True and entries[-1]["op"] == "videos.insert"


def test_upload_dir_blocks_files_outside_it(call, config, tmp_path):
    allowed = tmp_path / "videos"
    allowed.mkdir()
    config.upload_dir = allowed.resolve()
    outside = _video_file(tmp_path, size=10)
    result = call("youtube_upload_videos", videos=[{"source": str(outside), "title": "x"}])
    assert result["failed"] == 1
    assert "outside YOUTUBE_UPLOAD_DIR" in result["results"][0]["error"]
