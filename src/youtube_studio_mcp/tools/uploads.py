"""Video uploads: single and bulk, resumable, with optional thumbnail and playlist."""

from __future__ import annotations

from typing import Any

from ..client import YouTubeAPIError, YouTubeClient
from ..media import guess_mime
from ._common import READ, WRITE
from .videos import OWNER_PARTS

UPLOAD_NOTES = (
    "videos.insert has its own daily quota bucket (default 100 calls/day per Google Cloud "
    "project). Projects that haven't passed YouTube's API compliance audit may have uploads "
    "locked to private; check status.privacyStatus on the result."
)


def build_video_body(spec: dict[str, Any]) -> dict[str, Any]:
    """Turn the flat upload spec into a videos.insert resource body."""
    snippet = {
        "title": spec["title"],
        "description": spec.get("description"),
        "tags": spec.get("tags"),
        "categoryId": str(spec.get("category_id") or "22"),
        "defaultLanguage": spec.get("default_language"),
        "defaultAudioLanguage": spec.get("default_audio_language"),
    }
    status = {
        "privacyStatus": spec.get("privacy_status") or "private",
        "publishAt": spec.get("publish_at"),
        "selfDeclaredMadeForKids": bool(spec.get("made_for_kids", False)),
        "containsSyntheticMedia": spec.get("contains_synthetic_media"),
        "embeddable": spec.get("embeddable"),
        "publicStatsViewable": spec.get("public_stats_viewable"),
        "license": spec.get("license"),
    }
    if status["publishAt"]:
        status["privacyStatus"] = "private"  # scheduled videos must start private
    body: dict[str, Any] = {
        "snippet": {k: v for k, v in snippet.items() if v is not None},
        "status": {k: v for k, v in status.items() if v is not None},
    }
    if spec.get("recording_date"):
        body["recordingDetails"] = {"recordingDate": spec["recording_date"]}
    if spec.get("has_paid_product_placement") is not None:
        body["paidProductPlacementDetails"] = {
            "hasPaidProductPlacement": bool(spec["has_paid_product_placement"])
        }
    return body


def upload_one(client: YouTubeClient, spec: dict[str, Any]) -> dict[str, Any]:
    if not spec.get("source"):
        raise ValueError("Each video needs a `source` (local path or http(s) URL).")
    if not spec.get("title"):
        raise ValueError("Each video needs a `title` (max 100 characters).")
    if len(spec["title"]) > 100:
        raise ValueError("title is longer than 100 characters.")
    body = build_video_body(spec)
    with client.media(spec["source"]) as path:
        video = client.upload(
            "videos",
            file_path=path,
            mime_type=guess_mime(path),
            params={"part": ",".join(body), "notifySubscribers": spec.get("notify_subscribers")},
            metadata=body,
            op="videos.insert",
        )
    result: dict[str, Any] = {"source": spec["source"], "video": video}
    video_id = video.get("id")
    if video.get("_dry_run") or not video_id:
        return result
    result["video_id"] = video_id
    result["url"] = f"https://www.youtube.com/watch?v={video_id}"
    if spec.get("thumbnail"):
        with client.media(spec["thumbnail"]) as thumb:
            result["thumbnail"] = client.upload(
                "thumbnails/set",
                file_path=thumb,
                mime_type=guess_mime(thumb, "image/jpeg"),
                params={"videoId": video_id},
                op="thumbnails.set",
            )
    for playlist_id in spec.get("playlist_ids") or []:
        result.setdefault("playlists", []).append(
            client.request(
                "POST",
                "playlistItems",
                params={"part": "snippet"},
                json_body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
                op="playlistItems.insert",
            )
        )
    return result


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(annotations=WRITE)
    def youtube_upload_video(
        source: str,
        title: str,
        description: str | None = None,
        tags: list[str] | None = None,
        category_id: str = "22",
        privacy_status: str = "private",
        publish_at: str | None = None,
        made_for_kids: bool = False,
        contains_synthetic_media: bool | None = None,
        has_paid_product_placement: bool | None = None,
        default_language: str | None = None,
        default_audio_language: str | None = None,
        embeddable: bool | None = None,
        public_stats_viewable: bool | None = None,
        license: str | None = None,
        recording_date: str | None = None,
        notify_subscribers: bool | None = None,
        thumbnail: str | None = None,
        playlist_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upload a video to the authenticated YouTube channel (resumable, any size up to 256 GB).

        source: absolute local file path or http(s) URL (downloaded to a temp file first).
        privacy_status defaults to "private"; use "unlisted" for ad-only videos or "public".
        publish_at (RFC 3339) schedules the video; it stays private until then.
        contains_synthetic_media: set true for realistic AI-generated or altered content.
        thumbnail: optional image path/URL set after upload. playlist_ids: playlists to add it to.
        The video is processed after upload; poll youtube_get_upload_status for the result.
        """
        spec = {k: v for k, v in locals().items() if k != "client"}
        result = upload_one(client, spec)
        result["notes"] = UPLOAD_NOTES
        return result

    @mcp.tool(annotations=WRITE)
    def youtube_upload_videos(
        videos: list[dict[str, Any]], stop_on_error: bool = False
    ) -> dict[str, Any]:
        """Bulk-upload videos one after another. Each item takes the same keys as
        youtube_upload_video: {"source", "title", "description", "tags", "category_id",
        "privacy_status", "publish_at", "made_for_kids", "contains_synthetic_media",
        "has_paid_product_placement", "default_language", "default_audio_language",
        "notify_subscribers", "thumbnail", "playlist_ids", ...}.

        Failures are reported per item and don't stop the batch unless stop_on_error=true.
        A quota error stops the batch, since every later upload would fail too.
        """
        results: list[dict[str, Any]] = []
        for index, spec in enumerate(videos):
            try:
                results.append({"index": index, "ok": True, **upload_one(client, spec)})
            except (YouTubeAPIError, ValueError, RuntimeError, OSError) as e:
                results.append(
                    {"index": index, "ok": False, "source": spec.get("source"), "error": str(e)}
                )
                quota = isinstance(e, YouTubeAPIError) and e.reason in {
                    "quotaExceeded",
                    "uploadLimitExceeded",
                    "dailyLimitExceeded",
                }
                if stop_on_error or quota:
                    break
        uploaded = [r for r in results if r["ok"]]
        return {
            "requested": len(videos),
            "uploaded": len(uploaded),
            "failed": len(results) - len(uploaded),
            "skipped": len(videos) - len(results),
            "video_ids": [r.get("video_id") for r in uploaded if r.get("video_id")],
            "results": results,
            "notes": UPLOAD_NOTES,
        }

    @mcp.tool(annotations=READ)
    def youtube_get_upload_status(video_ids: list[str]) -> dict[str, Any]:
        """Check processing for uploaded videos: uploadStatus (uploaded/processed/rejected/failed),
        failure or rejection reason, privacy, processing progress and YouTube's suggestions."""
        resp = client.request("GET", "videos", params={"part": OWNER_PARTS, "id": video_ids})
        found = {v["id"]: v for v in resp.get("items", [])}
        out = []
        for vid in video_ids:
            v = found.get(vid)
            if not v:
                out.append({"video_id": vid, "found": False})
                continue
            status = v.get("status", {})
            processing = v.get("processingDetails", {})
            out.append(
                {
                    "video_id": vid,
                    "found": True,
                    "title": v.get("snippet", {}).get("title"),
                    "upload_status": status.get("uploadStatus"),
                    "failure_reason": status.get("failureReason"),
                    "rejection_reason": status.get("rejectionReason"),
                    "privacy_status": status.get("privacyStatus"),
                    "publish_at": status.get("publishAt"),
                    "processing_status": processing.get("processingStatus"),
                    "processing_progress": processing.get("processingProgress"),
                    "processing_failure_reason": processing.get("processingFailureReason"),
                    "duration": v.get("contentDetails", {}).get("duration"),
                    "suggestions": v.get("suggestions"),
                    "url": f"https://www.youtube.com/watch?v={vid}",
                }
            )
        return {"videos": out}
