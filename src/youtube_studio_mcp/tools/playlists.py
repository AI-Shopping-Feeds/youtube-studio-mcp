"""Playlists, playlist items and playlist cover images."""

from __future__ import annotations

from typing import Any

from ..client import YouTubeClient
from ..media import guess_mime
from ._common import DESTRUCTIVE, READ, WRITE, parts_of, require_confirm


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(annotations=READ)
    def youtube_list_playlists(
        mine: bool | None = True,
        channel_id: str | None = None,
        id: list[str] | None = None,
        part: str = "snippet,contentDetails,status",
        max_results: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List your playlists (default), a channel's playlists, or playlists by ID."""
        return client.request(
            "GET",
            "playlists",
            params={
                "part": part,
                "mine": None if (channel_id or id) else mine,
                "channelId": channel_id,
                "id": id,
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(annotations=WRITE)
    def youtube_create_playlist(
        title: str,
        description: str | None = None,
        privacy_status: str = "private",
        tags: list[str] | None = None,
        default_language: str | None = None,
    ) -> dict[str, Any]:
        """Create a playlist. privacy_status: public | unlisted | private."""
        snippet = {
            "title": title,
            "description": description,
            "tags": tags,
            "defaultLanguage": default_language,
        }
        body = {
            "snippet": {k: v for k, v in snippet.items() if v is not None},
            "status": {"privacyStatus": privacy_status},
        }
        return client.request(
            "POST",
            "playlists",
            params={"part": "snippet,status"},
            json_body=body,
            op="playlists.insert",
        )

    @mcp.tool(annotations=WRITE)
    def youtube_update_playlist(playlist: dict[str, Any]) -> dict[str, Any]:
        """Update a playlist resource. Include `id` and the full parts you change
        (e.g. snippet with title, status with privacyStatus)."""
        return client.request(
            "PUT",
            "playlists",
            params={"part": parts_of(playlist)},
            json_body=playlist,
            op="playlists.update",
        )

    @mcp.tool(annotations=DESTRUCTIVE)
    def youtube_delete_playlist(playlist_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a playlist (the videos stay). Requires confirm=true."""
        require_confirm(confirm, "Deleting a playlist")
        return client.request("DELETE", "playlists", params={"id": playlist_id})

    @mcp.tool(annotations=READ)
    def youtube_list_playlist_items(
        playlist_id: str,
        max_results: int = 50,
        max_pages: int = 1,
        video_id: str | None = None,
    ) -> dict[str, Any]:
        """List the videos in a playlist. Raise max_pages to read more than 50."""
        return client.paginate(
            "playlistItems",
            params={
                "part": "snippet,contentDetails,status",
                "playlistId": playlist_id,
                "maxResults": max_results,
                "videoId": video_id,
            },
            max_pages=max_pages,
        )

    @mcp.tool(annotations=WRITE)
    def youtube_add_to_playlist(
        playlist_id: str, video_ids: list[str], position: int | None = None
    ) -> dict[str, Any]:
        """Add videos to a playlist, in order. position: 0-based insert point (manual-sort
        playlists only)."""
        results = []
        for offset, video_id in enumerate(video_ids):
            snippet: dict[str, Any] = {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
            if position is not None:
                snippet["position"] = position + offset
            results.append(
                client.request(
                    "POST",
                    "playlistItems",
                    params={"part": "snippet"},
                    json_body={"snippet": snippet},
                    op="playlistItems.insert",
                )
            )
        return {"added": len(results), "items": results}

    @mcp.tool(annotations=WRITE)
    def youtube_update_playlist_item(playlist_item: dict[str, Any]) -> dict[str, Any]:
        """Update a playlist item (e.g. move it: snippet.position, or contentDetails.note).
        Include `id` and the full snippet (playlistId and resourceId are required)."""
        return client.request(
            "PUT",
            "playlistItems",
            params={"part": parts_of(playlist_item)},
            json_body=playlist_item,
        )

    @mcp.tool(annotations=DESTRUCTIVE)
    def youtube_remove_playlist_item(
        playlist_item_id: str, confirm: bool = False
    ) -> dict[str, Any]:
        """Remove an item from a playlist (playlist item ID, not video ID). Requires confirm."""
        require_confirm(confirm, "Removing a playlist item")
        return client.request("DELETE", "playlistItems", params={"id": playlist_item_id})

    @mcp.tool(annotations=READ)
    def youtube_list_playlist_images(playlist_id: str) -> dict[str, Any]:
        """List a playlist's custom cover images."""
        return client.request(
            "GET", "playlistImages", params={"part": "snippet", "parent": playlist_id}
        )

    @mcp.tool(annotations=WRITE)
    def youtube_set_playlist_image(
        playlist_id: str, image: str, playlist_image_id: str | None = None
    ) -> dict[str, Any]:
        """Upload a playlist cover image (local path or URL, JPEG/PNG, max 50 MB). Pass
        playlist_image_id to replace an existing image instead of adding one."""
        body: dict[str, Any] = {"snippet": {"playlistId": playlist_id, "type": "hero"}}
        if playlist_image_id:
            body["id"] = playlist_image_id
        with client.media(image) as path:
            return client.upload(
                "playlistImages",
                method="PUT" if playlist_image_id else "POST",
                file_path=path,
                mime_type=guess_mime(path, "image/jpeg"),
                params={"part": "snippet"},
                metadata=body,
            )

    @mcp.tool(annotations=DESTRUCTIVE)
    def youtube_delete_playlist_image(
        playlist_image_id: str, confirm: bool = False
    ) -> dict[str, Any]:
        """Delete a playlist cover image. Requires confirm=true."""
        require_confirm(confirm, "Deleting a playlist image")
        return client.request("DELETE", "playlistImages", params={"id": playlist_image_id})
