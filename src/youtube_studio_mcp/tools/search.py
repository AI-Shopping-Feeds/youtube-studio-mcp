"""Search, memberships, Super Chat events, third-party links and abuse reports."""

from __future__ import annotations

from typing import Any

from ..client import YouTubeClient
from ._common import DESTRUCTIVE, READ, WRITE, merge, parts_of, require_confirm


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(annotations=READ)
    def youtube_search(
        q: str | None = None,
        type: str = "video",
        channel_id: str | None = None,
        for_mine: bool | None = None,
        order: str | None = None,
        published_after: str | None = None,
        published_before: str | None = None,
        region_code: str | None = None,
        relevance_language: str | None = None,
        video_duration: str | None = None,
        event_type: str | None = None,
        safe_search: str | None = None,
        max_results: int = 25,
        page_token: str | None = None,
        extra_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search YouTube for videos, channels or playlists (search.list).

        Costs 100 quota units and has its own daily bucket, so prefer youtube_list_videos or
        youtube_list_playlist_items for your own content. type: video | channel | playlist
        (comma-separate for several). order: date | rating | relevance | title | videoCount |
        viewCount. for_mine=true searches your own videos (type must be video).
        extra_params passes any other search.list parameter (e.g. videoCategoryId, location).
        """
        return client.request(
            "GET",
            "search",
            params=merge(
                {
                    "part": "snippet",
                    "q": q,
                    "type": type,
                    "channelId": channel_id,
                    "forMine": for_mine,
                    "order": order,
                    "publishedAfter": published_after,
                    "publishedBefore": published_before,
                    "regionCode": region_code,
                    "relevanceLanguage": relevance_language,
                    "videoDuration": video_duration,
                    "eventType": event_type,
                    "safeSearch": safe_search,
                    "maxResults": max_results,
                    "pageToken": page_token,
                },
                extra_params,
            ),
        )

    @mcp.tool(annotations=READ)
    def youtube_list_members(
        mode: str = "all_current",
        has_access_to_level: str | None = None,
        filter_by_member_channel_id: list[str] | None = None,
        max_results: int = 100,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List channel members (memberships). Needs the memberships scope:
        `youtube-studio-mcp auth-init --extra-scope memberships`."""
        return client.request(
            "GET",
            "members",
            params={
                "part": "snippet",
                "mode": mode,
                "hasAccessToLevel": has_access_to_level,
                "filterByMemberChannelId": filter_by_member_channel_id,
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(annotations=READ)
    def youtube_list_membership_levels() -> dict[str, Any]:
        """List the channel's membership levels (needs the memberships scope)."""
        return client.request("GET", "membershipsLevels", params={"part": "id,snippet"})

    @mcp.tool(annotations=READ)
    def youtube_list_super_chat_events(
        hl: str | None = None, max_results: int = 50, page_token: str | None = None
    ) -> dict[str, Any]:
        """List Super Chat and Super Sticker events from the channel's live streams (last 30 days)."""
        return client.request(
            "GET",
            "superChatEvents",
            params={
                "part": "snippet",
                "hl": hl,
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(annotations=READ)
    def youtube_list_third_party_links(
        type: str | None = None,
        linking_token: str | None = None,
        external_channel_id: str | None = None,
    ) -> dict[str, Any]:
        """List the channel's links to third parties, such as a linked merchant store
        (type: channelToStoreLink | channelToAffiliateProgramLink)."""
        return client.request(
            "GET",
            "thirdPartyLinks",
            params={
                "part": "snippet,status",
                "type": type,
                "linkingToken": linking_token,
                "externalChannelId": external_channel_id,
            },
        )

    @mcp.tool(annotations=WRITE)
    def youtube_upsert_third_party_link(
        link: dict[str, Any], update: bool = False
    ) -> dict[str, Any]:
        """Create (or with update=true, update) a third-party link resource, e.g. a
        channel-to-store link. See the thirdPartyLinks reference for the body shape."""
        return client.request(
            "PUT" if update else "POST",
            "thirdPartyLinks",
            params={"part": parts_of(link)},
            json_body=link,
        )

    @mcp.tool(annotations=DESTRUCTIVE)
    def youtube_delete_third_party_link(
        linking_token: str, type: str, confirm: bool = False
    ) -> dict[str, Any]:
        """Remove a third-party link. Requires confirm=true."""
        require_confirm(confirm, "Removing a third-party link")
        return client.request(
            "DELETE", "thirdPartyLinks", params={"linkingToken": linking_token, "type": type}
        )

    @mcp.tool(annotations=WRITE)
    def youtube_report_abuse(report: dict[str, Any]) -> dict[str, Any]:
        """File an abuse report against any YouTube entity (abuseReports.insert). Body:
        {"snippet": {"subject": {"id": "...", "type": "..."}, "abuseTypes": [...],
        "description": "..."}}."""
        return client.request("POST", "abuseReports", params={"part": "snippet"}, json_body=report)
