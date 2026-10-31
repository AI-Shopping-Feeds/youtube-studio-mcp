"""Live Streaming API: broadcasts, streams, cuepoints and live chat."""

from __future__ import annotations

from typing import Any

from ..client import YouTubeClient
from ._common import DESTRUCTIVE, READ, WRITE, parts_of, require_confirm


def register(mcp, client: YouTubeClient) -> None:
    # ---- broadcasts ----

    @mcp.tool(title="List live broadcasts", annotations=READ)
    def youtube_list_live_broadcasts(
        broadcast_status: str | None = "all",
        id: list[str] | None = None,
        broadcast_type: str | None = None,
        max_results: int = 25,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List your live broadcasts. broadcast_status: active | all | completed | upcoming."""
        return client.request(
            "GET",
            "liveBroadcasts",
            params={
                "part": "snippet,status,contentDetails",
                "broadcastStatus": None if id else broadcast_status,
                "id": id,
                "broadcastType": broadcast_type,
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(title="Schedule a live broadcast", annotations=WRITE)
    def youtube_create_live_broadcast(
        title: str,
        scheduled_start_time: str,
        description: str | None = None,
        privacy_status: str = "private",
        scheduled_end_time: str | None = None,
        enable_auto_start: bool | None = None,
        enable_auto_stop: bool | None = None,
        enable_dvr: bool | None = None,
        made_for_kids: bool = False,
    ) -> dict[str, Any]:
        """Schedule a live broadcast (times are RFC 3339). Bind it to a stream with
        youtube_bind_live_broadcast, then go live with youtube_transition_live_broadcast."""
        snippet = {
            "title": title,
            "description": description,
            "scheduledStartTime": scheduled_start_time,
            "scheduledEndTime": scheduled_end_time,
        }
        content = {
            "enableAutoStart": enable_auto_start,
            "enableAutoStop": enable_auto_stop,
            "enableDvr": enable_dvr,
        }
        body = {
            "snippet": {k: v for k, v in snippet.items() if v is not None},
            "status": {"privacyStatus": privacy_status, "selfDeclaredMadeForKids": made_for_kids},
            "contentDetails": {k: v for k, v in content.items() if v is not None},
        }
        return client.request(
            "POST",
            "liveBroadcasts",
            params={"part": parts_of(body)},
            json_body=body,
            op="liveBroadcasts.insert",
        )

    @mcp.tool(title="Update a live broadcast", annotations=WRITE)
    def youtube_update_live_broadcast(broadcast: dict[str, Any]) -> dict[str, Any]:
        """Update a live broadcast resource. Include `id` and the full parts you change."""
        return client.request(
            "PUT", "liveBroadcasts", params={"part": parts_of(broadcast)}, json_body=broadcast
        )

    @mcp.tool(title="Bind a broadcast to a stream", annotations=WRITE)
    def youtube_bind_live_broadcast(
        broadcast_id: str, stream_id: str | None = None
    ) -> dict[str, Any]:
        """Bind a broadcast to a live stream (omit stream_id to unbind)."""
        return client.request(
            "POST",
            "liveBroadcasts/bind",
            params={"id": broadcast_id, "part": "id,contentDetails", "streamId": stream_id},
        )

    @mcp.tool(title="Change a broadcast's state", annotations=DESTRUCTIVE)
    def youtube_transition_live_broadcast(
        broadcast_id: str, broadcast_status: str
    ) -> dict[str, Any]:
        """Change a broadcast's state. broadcast_status: testing | live | complete.
        "complete" ends the broadcast for good; it can't be restarted."""
        return client.request(
            "POST",
            "liveBroadcasts/transition",
            params={
                "id": broadcast_id,
                "broadcastStatus": broadcast_status,
                "part": "id,snippet,status",
            },
        )

    @mcp.tool(title="Insert a live ad break", annotations=WRITE)
    def youtube_insert_cuepoint(
        broadcast_id: str, duration_secs: int = 30, insertion_offset_time_ms: int | None = None
    ) -> dict[str, Any]:
        """Insert an ad break (cuepoint) into a live broadcast."""
        body: dict[str, Any] = {"cueType": "cueTypeAd", "durationSecs": duration_secs}
        if insertion_offset_time_ms is not None:
            body["insertionOffsetTimeMs"] = str(insertion_offset_time_ms)
        return client.request(
            "POST", "liveBroadcasts/cuepoint", params={"id": broadcast_id}, json_body=body
        )

    @mcp.tool(title="Delete a live broadcast", annotations=DESTRUCTIVE)
    def youtube_delete_live_broadcast(broadcast_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a broadcast. Requires confirm=true."""
        require_confirm(confirm, "Deleting a live broadcast")
        return client.request("DELETE", "liveBroadcasts", params={"id": broadcast_id})

    # ---- streams ----

    @mcp.tool(title="List live streams", annotations=READ)
    def youtube_list_live_streams(
        mine: bool | None = True,
        id: list[str] | None = None,
        max_results: int = 25,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List your live streams (ingestion settings, stream keys and health)."""
        return client.request(
            "GET",
            "liveStreams",
            params={
                "part": "snippet,cdn,contentDetails,status",
                "mine": None if id else mine,
                "id": id,
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(title="Create a live stream", annotations=WRITE)
    def youtube_create_live_stream(
        title: str,
        resolution: str = "variable",
        frame_rate: str = "variable",
        ingestion_type: str = "rtmp",
        is_reusable: bool = True,
    ) -> dict[str, Any]:
        """Create a live stream (returns the ingestion address and stream key)."""
        body = {
            "snippet": {"title": title},
            "cdn": {
                "resolution": resolution,
                "frameRate": frame_rate,
                "ingestionType": ingestion_type,
            },
            "contentDetails": {"isReusable": is_reusable},
        }
        return client.request(
            "POST", "liveStreams", params={"part": "snippet,cdn,contentDetails"}, json_body=body
        )

    @mcp.tool(title="Update a live stream", annotations=WRITE)
    def youtube_update_live_stream(stream: dict[str, Any]) -> dict[str, Any]:
        """Update a live stream resource. Include `id` and the full parts you change."""
        return client.request(
            "PUT", "liveStreams", params={"part": parts_of(stream)}, json_body=stream
        )

    @mcp.tool(title="Delete a live stream", annotations=DESTRUCTIVE)
    def youtube_delete_live_stream(stream_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a live stream. Requires confirm=true."""
        require_confirm(confirm, "Deleting a live stream")
        return client.request("DELETE", "liveStreams", params={"id": stream_id})

    # ---- live chat ----

    @mcp.tool(title="Read live chat messages", annotations=READ)
    def youtube_list_live_chat_messages(
        live_chat_id: str,
        page_token: str | None = None,
        max_results: int = 200,
        hl: str | None = None,
    ) -> dict[str, Any]:
        """Read a live chat (liveChatId is on the broadcast's snippet). Poll again with
        nextPageToken after pollingIntervalMillis."""
        return client.request(
            "GET",
            "liveChat/messages",
            params={
                "liveChatId": live_chat_id,
                "part": "snippet,authorDetails",
                "pageToken": page_token,
                "maxResults": max_results,
                "hl": hl,
            },
        )

    @mcp.tool(title="Post a live chat message", annotations=WRITE)
    def youtube_post_live_chat_message(live_chat_id: str, text: str) -> dict[str, Any]:
        """Post a text message to a live chat."""
        body = {
            "snippet": {
                "liveChatId": live_chat_id,
                "type": "textMessageEvent",
                "textMessageDetails": {"messageText": text},
            }
        }
        return client.request(
            "POST", "liveChat/messages", params={"part": "snippet"}, json_body=body
        )

    @mcp.tool(title="Delete a live chat message", annotations=DESTRUCTIVE)
    def youtube_delete_live_chat_message(message_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a live chat message. Requires confirm=true."""
        require_confirm(confirm, "Deleting a chat message")
        return client.request("DELETE", "liveChat/messages", params={"id": message_id})

    @mcp.tool(title="Close a live chat poll", annotations=DESTRUCTIVE)
    def youtube_close_live_chat_poll(poll_id: str) -> dict[str, Any]:
        """Close a live chat poll (liveChatMessages.transition, status=closed). A closed poll
        can't be reopened."""
        return client.request(
            "POST", "liveChat/messages/transition", params={"id": poll_id, "status": "closed"}
        )

    @mcp.tool(title="List live chat moderators", annotations=READ)
    def youtube_list_live_chat_moderators(
        live_chat_id: str, max_results: int = 50, page_token: str | None = None
    ) -> dict[str, Any]:
        """List a live chat's moderators."""
        return client.request(
            "GET",
            "liveChat/moderators",
            params={
                "liveChatId": live_chat_id,
                "part": "snippet",
                "maxResults": max_results,
                "pageToken": page_token,
            },
        )

    @mcp.tool(title="Add a live chat moderator", annotations=WRITE)
    def youtube_add_live_chat_moderator(live_chat_id: str, channel_id: str) -> dict[str, Any]:
        """Make a channel a moderator of a live chat."""
        body = {
            "snippet": {"liveChatId": live_chat_id, "moderatorDetails": {"channelId": channel_id}}
        }
        return client.request(
            "POST", "liveChat/moderators", params={"part": "snippet"}, json_body=body
        )

    @mcp.tool(title="Remove a live chat moderator", annotations=DESTRUCTIVE)
    def youtube_remove_live_chat_moderator(
        moderator_id: str, confirm: bool = False
    ) -> dict[str, Any]:
        """Remove a live chat moderator. Requires confirm=true."""
        require_confirm(confirm, "Removing a moderator")
        return client.request("DELETE", "liveChat/moderators", params={"id": moderator_id})

    @mcp.tool(title="Ban a live chat user", annotations=WRITE)
    def youtube_ban_live_chat_user(
        live_chat_id: str, channel_id: str, ban_duration_seconds: int | None = None
    ) -> dict[str, Any]:
        """Ban a user from a live chat: permanently, or temporarily with ban_duration_seconds."""
        snippet: dict[str, Any] = {
            "liveChatId": live_chat_id,
            "type": "temporary" if ban_duration_seconds else "permanent",
            "bannedUserDetails": {"channelId": channel_id},
        }
        if ban_duration_seconds:
            snippet["banDurationSeconds"] = str(ban_duration_seconds)
        return client.request(
            "POST", "liveChat/bans", params={"part": "snippet"}, json_body={"snippet": snippet}
        )

    @mcp.tool(title="Unban a live chat user", annotations=WRITE)
    def youtube_unban_live_chat_user(ban_id: str) -> dict[str, Any]:
        """Lift a live chat ban (use the ban ID returned by youtube_ban_live_chat_user)."""
        return client.request("DELETE", "liveChat/bans", params={"id": ban_id})
