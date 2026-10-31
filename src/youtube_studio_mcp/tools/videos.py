"""Read, edit, rate, report and delete videos; thumbnails; categories."""

from __future__ import annotations

from typing import Any

from ..client import YouTubeClient
from ..media import guess_mime
from ._common import DESTRUCTIVE, READ, WRITE, merge, parts_of, require_confirm

VIDEO_PARTS = "snippet,statistics,status,contentDetails"
OWNER_PARTS = "snippet,status,contentDetails,statistics,fileDetails,processingDetails,suggestions"


def uploads_playlist_id(client: YouTubeClient) -> str:
    channel = client.request("GET", "channels", params={"part": "contentDetails", "mine": True})
    items = channel.get("items") or []
    if not items:
        raise RuntimeError("No YouTube channel for the authenticated account.")
    playlist = items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if not playlist:
        raise RuntimeError("Could not find the uploads playlist for the authenticated channel.")
    return playlist


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(annotations=READ)
    def youtube_list_videos(max_results: int = 10, page_token: str | None = None) -> dict[str, Any]:
        """List your channel's uploads, newest first, with metadata, status and statistics.
        Includes private, unlisted and scheduled videos."""
        playlist = client.request(
            "GET",
            "playlistItems",
            params={
                "part": "snippet,contentDetails,status",
                "playlistId": uploads_playlist_id(client),
                "maxResults": max(1, min(max_results, 50)),
                "pageToken": page_token,
            },
        )
        ids = [
            i["contentDetails"]["videoId"]
            for i in playlist.get("items", [])
            if i.get("contentDetails", {}).get("videoId")
        ]
        details: dict[str, Any] = {}
        if ids:
            resp = client.request("GET", "videos", params={"part": VIDEO_PARTS, "id": ids})
            details = {v["id"]: v for v in resp.get("items", [])}
        return {
            "items": [
                {
                    "playlistItem": i,
                    "details": details.get(i.get("contentDetails", {}).get("videoId")),
                }
                for i in playlist.get("items", [])
            ],
            "nextPageToken": playlist.get("nextPageToken"),
            "pageInfo": playlist.get("pageInfo", {}),
        }

    @mcp.tool(annotations=READ)
    def youtube_get_video(video_id: str, part: str = VIDEO_PARTS) -> dict[str, Any]:
        """Get one video. For your own videos you can add fileDetails, processingDetails,
        suggestions, recordingDetails, localizations, paidProductPlacementDetails to `part`."""
        items = client.request("GET", "videos", params={"part": part, "id": video_id}).get("items")
        if not items:
            raise RuntimeError(f"Video {video_id} not found.")
        return items[0]

    @mcp.tool(annotations=READ)
    def youtube_videos_list(
        id: list[str] | None = None,
        chart: str | None = None,
        my_rating: str | None = None,
        part: str = VIDEO_PARTS,
        region_code: str | None = None,
        video_category_id: str | None = None,
        hl: str | None = None,
        max_results: int = 25,
        page_token: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """videos.list: fetch up to 50 videos by ID, the mostPopular chart, or videos you rated
        (my_rating=like|dislike). 1 quota unit."""
        return client.request(
            "GET",
            "videos",
            params=merge(
                {
                    "part": part,
                    "id": id,
                    "chart": chart,
                    "myRating": my_rating,
                    "regionCode": region_code,
                    "videoCategoryId": video_category_id,
                    "hl": hl,
                    "maxResults": None if id else max_results,
                    "pageToken": page_token,
                },
                extra_params,
            ),
        )

    @mcp.tool(annotations=READ)
    def youtube_batch_get_video_stats(
        video_ids: list[str], part: str | None = None
    ) -> dict[str, Any]:
        """Get statistics for many videos at once (videos:batchGetStats, own 10,000/day bucket)."""
        return client.request("GET", "videos:batchGetStats", params={"id": video_ids, "part": part})

    @mcp.tool(annotations=WRITE)
    def youtube_update_video(
        video_id: str,
        title: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        category_id: str | None = None,
        default_language: str | None = None,
        default_audio_language: str | None = None,
        privacy_status: str | None = None,
        publish_at: str | None = None,
        embeddable: bool | None = None,
        public_stats_viewable: bool | None = None,
        made_for_kids: bool | None = None,
        contains_synthetic_media: bool | None = None,
        license: str | None = None,
    ) -> dict[str, Any]:
        """Update a video's title, description, tags, category, languages and status.

        Only the fields you pass change; the rest are read first and sent back unchanged.
        privacy_status: public | unlisted | private. publish_at (RFC 3339) schedules a
        private video to go public. 50 quota units.
        """
        existing = client.request(
            "GET", "videos", params={"part": "snippet,status", "id": video_id}
        ).get("items")
        if not existing:
            raise RuntimeError(f"Video {video_id} not found.")
        snippet = existing[0]["snippet"]
        status = existing[0]["status"]
        snippet_updates = {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": default_language,
            "defaultAudioLanguage": default_audio_language,
        }
        status_updates = {
            "privacyStatus": privacy_status,
            "publishAt": publish_at,
            "embeddable": embeddable,
            "publicStatsViewable": public_stats_viewable,
            "selfDeclaredMadeForKids": made_for_kids,
            "containsSyntheticMedia": contains_synthetic_media,
            "license": license,
        }
        snippet.update({k: v for k, v in snippet_updates.items() if v is not None})
        status.update({k: v for k, v in status_updates.items() if v is not None})
        # Read-only fields the API rejects on update.
        for key in (
            "thumbnails",
            "localized",
            "channelId",
            "channelTitle",
            "publishedAt",
            "liveBroadcastContent",
        ):
            snippet.pop(key, None)
        for key in ("uploadStatus", "failureReason", "rejectionReason", "madeForKids"):
            status.pop(key, None)
        return client.request(
            "PUT",
            "videos",
            params={"part": "snippet,status"},
            json_body={"id": video_id, "snippet": snippet, "status": status},
            op="videos.update",
        )

    @mcp.tool(annotations=WRITE)
    def youtube_update_video_resource(
        video: dict[str, Any], part: str | None = None
    ) -> dict[str, Any]:
        """Raw videos.update for fields youtube_update_video doesn't cover (recordingDetails,
        localizations, paidProductPlacementDetails...). `video` must include `id`; each part you
        send is replaced in full."""
        return client.request(
            "PUT",
            "videos",
            params={"part": part or parts_of(video)},
            json_body=video,
            op="videos.update",
        )

    @mcp.tool(annotations=DESTRUCTIVE)
    def youtube_delete_video(video_id: str, confirm: bool = False) -> dict[str, Any]:
        """Permanently delete one of your videos. Requires confirm=true."""
        require_confirm(confirm, "Deleting a video")
        return client.request("DELETE", "videos", params={"id": video_id}, op="videos.delete")

    @mcp.tool(annotations=WRITE)
    def youtube_rate_video(video_id: str, rating: str) -> dict[str, Any]:
        """Like, dislike or clear your rating on a video. rating: like | dislike | none."""
        return client.request("POST", "videos/rate", params={"id": video_id, "rating": rating})

    @mcp.tool(annotations=READ)
    def youtube_get_video_rating(video_ids: list[str]) -> dict[str, Any]:
        """Get your rating (like/dislike/none) for up to 50 videos."""
        return client.request("GET", "videos/getRating", params={"id": video_ids})

    @mcp.tool(annotations=WRITE)
    def youtube_report_video_abuse(
        video_id: str,
        reason_id: str,
        secondary_reason_id: str | None = None,
        comments: str | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Report a video for abuse. Get reason IDs from youtube_list_video_abuse_reasons."""
        body = {
            "videoId": video_id,
            "reasonId": reason_id,
            "secondaryReasonId": secondary_reason_id,
            "comments": comments,
            "language": language,
        }
        return client.request(
            "POST", "videos/reportAbuse", json_body={k: v for k, v in body.items() if v is not None}
        )

    @mcp.tool(annotations=READ)
    def youtube_get_video_trainability(video_id: str) -> dict[str, Any]:
        """Show which third parties a video's owner allows to train AI models on it."""
        return client.request("GET", "videoTrainability", params={"id": video_id})

    @mcp.tool(annotations=WRITE)
    def youtube_upload_thumbnail(video_id: str, image: str) -> dict[str, Any]:
        """Set a custom thumbnail from a local image path or URL (JPEG/PNG, max 50 MB,
        1280x720 recommended). The channel must be verified for custom thumbnails."""
        with client.media(image) as path:
            return client.upload(
                "thumbnails/set",
                file_path=path,
                mime_type=guess_mime(path, "image/jpeg"),
                params={"videoId": video_id},
                op="thumbnails.set",
            )

    @mcp.tool(annotations=READ)
    def youtube_list_video_categories(
        region_code: str = "US", hl: str | None = None
    ) -> dict[str, Any]:
        """List video category IDs (e.g. 22 People & Blogs, 26 Howto & Style) for a region."""
        return client.request(
            "GET",
            "videoCategories",
            params={"part": "snippet", "regionCode": region_code, "hl": hl},
        )

    @mcp.tool(annotations=READ)
    def youtube_list_video_abuse_reasons(hl: str | None = None) -> dict[str, Any]:
        """List the reasons accepted by youtube_report_video_abuse."""
        return client.request(
            "GET", "videoAbuseReportReasons", params={"part": "snippet", "hl": hl}
        )

    @mcp.tool(annotations=READ)
    def youtube_list_languages(hl: str | None = None) -> dict[str, Any]:
        """List the interface languages YouTube supports (i18nLanguages)."""
        return client.request("GET", "i18nLanguages", params={"part": "snippet", "hl": hl})

    @mcp.tool(annotations=READ)
    def youtube_list_regions(hl: str | None = None) -> dict[str, Any]:
        """List the content regions YouTube supports (i18nRegions)."""
        return client.request("GET", "i18nRegions", params={"part": "snippet", "hl": hl})
