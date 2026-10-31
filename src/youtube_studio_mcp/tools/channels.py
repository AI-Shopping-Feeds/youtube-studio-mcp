"""Channels, channel sections, banners, watermarks, activities and subscriptions."""

from __future__ import annotations

from typing import Any

from ..client import YouTubeClient
from ..media import guess_mime
from ._common import DESTRUCTIVE, READ, WRITE, merge, parts_of, require_confirm


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(title="Get channel overview", annotations=READ)
    def youtube_channel_overview() -> dict[str, Any]:
        """Get the authenticated channel: profile, branding, statistics and uploads playlist ID."""
        return client.request(
            "GET",
            "channels",
            params={
                "part": "snippet,statistics,brandingSettings,contentDetails,status,topicDetails",
                "mine": True,
            },
        )

    @mcp.tool(title="List channels", annotations=READ)
    def youtube_list_channels(
        part: str = "snippet,statistics,contentDetails",
        mine: bool | None = None,
        id: list[str] | None = None,
        for_handle: str | None = None,
        for_username: str | None = None,
        managed_by_me: bool | None = None,
        max_results: int = 50,
        page_token: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List channels by ID, handle (e.g. "@GoogleDevelopers"), username, or your own (mine=true).
        Costs 1 quota unit."""
        return client.request(
            "GET",
            "channels",
            params=merge(
                {
                    "part": part,
                    "mine": mine,
                    "id": id,
                    "forHandle": for_handle,
                    "forUsername": for_username,
                    "managedByMe": managed_by_me,
                    "maxResults": max_results,
                    "pageToken": page_token,
                },
                extra_params,
            ),
        )

    @mcp.tool(title="Update a channel", annotations=WRITE)
    def youtube_update_channel(channel: dict[str, Any], part: str | None = None) -> dict[str, Any]:
        """Update a channel resource (channels.update). `channel` must include `id`.

        Only brandingSettings, invideoPromotion and localizations are writable.
        Every writable field in the parts you send is replaced, so read the
        channel first and send the complete part.
        """
        return client.request(
            "PUT", "channels", params={"part": part or parts_of(channel)}, json_body=channel
        )

    @mcp.tool(title="Upload a channel banner", annotations=WRITE)
    def youtube_upload_channel_banner(
        source: str, apply_to_channel_id: str | None = None
    ) -> dict[str, Any]:
        """Upload a channel banner image (local path or URL; 16:9, at least 2048x1152, max 6 MB).

        Returns the banner URL. If apply_to_channel_id is given, the URL is also set as that
        channel's brandingSettings.image.bannerExternalUrl.
        """
        with client.media(source) as path:
            result = client.upload(
                "channelBanners/insert", file_path=path, mime_type=guess_mime(path, "image/jpeg")
            )
        if apply_to_channel_id and result.get("url"):
            channel = client.request(
                "GET", "channels", params={"part": "brandingSettings", "id": apply_to_channel_id}
            )
            items = channel.get("items") or []
            if not items:
                raise RuntimeError(f"Channel {apply_to_channel_id} not found.")
            body = {"id": apply_to_channel_id, "brandingSettings": items[0]["brandingSettings"]}
            body["brandingSettings"].setdefault("image", {})["bannerExternalUrl"] = result["url"]
            result["channel_update"] = client.request(
                "PUT", "channels", params={"part": "brandingSettings"}, json_body=body
            )
        return result

    @mcp.tool(title="Set the channel watermark", annotations=WRITE)
    def youtube_set_watermark(
        channel_id: str,
        source: str,
        timing_type: str = "offsetFromEnd",
        offset_ms: int = 15000,
        duration_ms: int | None = None,
    ) -> dict[str, Any]:
        """Set the channel's video watermark (branding image) from a local path or URL.

        timing_type: offsetFromStart | offsetFromEnd. offset_ms: when it appears.
        duration_ms: how long it shows (omit for the whole video).
        """
        timing: dict[str, Any] = {"type": timing_type, "offsetMs": str(offset_ms)}
        if duration_ms is not None:
            timing["durationMs"] = str(duration_ms)
        with client.media(source) as path:
            return client.upload(
                "watermarks/set",
                file_path=path,
                mime_type=guess_mime(path, "image/png"),
                params={"channelId": channel_id},
                metadata={
                    "timing": timing,
                    "position": {"type": "corner", "cornerPosition": "topRight"},
                },
            )

    @mcp.tool(title="Remove the channel watermark", annotations=DESTRUCTIVE)
    def youtube_unset_watermark(channel_id: str) -> dict[str, Any]:
        """Remove the channel's video watermark."""
        return client.request("POST", "watermarks/unset", params={"channelId": channel_id})

    # ---- channel sections ----

    @mcp.tool(title="List channel sections", annotations=READ)
    def youtube_list_channel_sections(
        part: str = "snippet,contentDetails",
        mine: bool | None = True,
        channel_id: str | None = None,
        id: list[str] | None = None,
        hl: str | None = None,
    ) -> dict[str, Any]:
        """List the shelves on a channel's home tab."""
        return client.request(
            "GET",
            "channelSections",
            params={
                "part": part,
                "mine": None if channel_id or id else mine,
                "channelId": channel_id,
                "id": id,
                "hl": hl,
            },
        )

    @mcp.tool(title="Create a channel section", annotations=WRITE)
    def youtube_create_channel_section(section: dict[str, Any]) -> dict[str, Any]:
        """Add a channel section. Example: {"snippet": {"type": "multiplePlaylists",
        "title": "Ads", "position": 1}, "contentDetails": {"playlists": ["PL..."]}}."""
        return client.request(
            "POST", "channelSections", params={"part": parts_of(section)}, json_body=section
        )

    @mcp.tool(title="Update a channel section", annotations=WRITE)
    def youtube_update_channel_section(section: dict[str, Any]) -> dict[str, Any]:
        """Update a channel section. `section` must include `id`."""
        return client.request(
            "PUT", "channelSections", params={"part": parts_of(section)}, json_body=section
        )

    @mcp.tool(title="Delete a channel section", annotations=DESTRUCTIVE)
    def youtube_delete_channel_section(section_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a channel section. Requires confirm=true."""
        require_confirm(confirm, "Deleting a channel section")
        return client.request("DELETE", "channelSections", params={"id": section_id})

    # ---- activities & subscriptions ----

    @mcp.tool(title="List channel activity", annotations=READ)
    def youtube_list_activities(
        mine: bool | None = True,
        channel_id: str | None = None,
        published_after: str | None = None,
        published_before: str | None = None,
        region_code: str | None = None,
        max_results: int = 25,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List channel activity (uploads, likes, playlist additions...). Dates are RFC 3339."""
        return client.request(
            "GET",
            "activities",
            params={
                "part": "snippet,contentDetails",
                "mine": None if channel_id else mine,
                "channelId": channel_id,
                "publishedAfter": published_after,
                "publishedBefore": published_before,
                "regionCode": region_code,
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(title="List subscriptions", annotations=READ)
    def youtube_list_subscriptions(
        mine: bool | None = True,
        my_subscribers: bool | None = None,
        channel_id: str | None = None,
        for_channel_id: list[str] | None = None,
        order: str | None = None,
        max_results: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List subscriptions: channels you subscribe to (mine), your recent subscribers
        (my_subscribers=true), or a channel's public subscriptions. order: alphabetical |
        relevance | unread."""
        return client.request(
            "GET",
            "subscriptions",
            params={
                "part": "snippet,contentDetails,subscriberSnippet",
                "mine": None if (channel_id or my_subscribers) else mine,
                "mySubscribers": my_subscribers,
                "channelId": channel_id,
                "forChannelId": for_channel_id,
                "order": order,
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(title="Subscribe to a channel", annotations=WRITE)
    def youtube_subscribe(channel_id: str) -> dict[str, Any]:
        """Subscribe the authenticated channel to another channel."""
        body = {"snippet": {"resourceId": {"kind": "youtube#channel", "channelId": channel_id}}}
        return client.request("POST", "subscriptions", params={"part": "snippet"}, json_body=body)

    @mcp.tool(title="Unsubscribe from a channel", annotations=DESTRUCTIVE)
    def youtube_unsubscribe(subscription_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a subscription (use the subscription ID, not the channel ID). Requires confirm."""
        require_confirm(confirm, "Unsubscribing")
        return client.request("DELETE", "subscriptions", params={"id": subscription_id})
