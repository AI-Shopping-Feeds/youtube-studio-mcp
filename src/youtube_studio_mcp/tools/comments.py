"""Comment threads, replies and moderation."""

from __future__ import annotations

from typing import Any

from ..client import YouTubeClient
from ._common import DESTRUCTIVE, READ, WRITE, require_confirm


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(title="List comments", annotations=READ)
    def youtube_list_comments(
        video_id: str | None = None,
        all_threads_related_to_channel_id: str | None = None,
        id: list[str] | None = None,
        search_terms: str | None = None,
        moderation_status: str | None = None,
        order: str = "time",
        max_results: int = 20,
        page_token: str | None = None,
        text_format: str = "plainText",
    ) -> dict[str, Any]:
        """List top-level comment threads (with replies) on a video, or across a channel.

        moderation_status: published | heldForReview | likelySpam (owner only).
        order: time | relevance.
        """
        return client.request(
            "GET",
            "commentThreads",
            params={
                "part": "snippet,replies",
                "videoId": video_id,
                "allThreadsRelatedToChannelId": all_threads_related_to_channel_id,
                "id": id,
                "searchTerms": search_terms,
                "moderationStatus": moderation_status,
                "order": None if id else order,
                "maxResults": None if id else max_results,
                "pageToken": page_token,
                "textFormat": text_format,
            },
        )

    @mcp.tool(title="List comment replies", annotations=READ)
    def youtube_list_comment_replies(
        parent_id: str, max_results: int = 20, page_token: str | None = None
    ) -> dict[str, Any]:
        """List replies to a top-level comment."""
        return client.request(
            "GET",
            "comments",
            params={
                "part": "snippet",
                "parentId": parent_id,
                "maxResults": max_results,
                "pageToken": page_token,
                "textFormat": "plainText",
            },
        )

    @mcp.tool(title="Post a comment", annotations=WRITE)
    def youtube_post_comment(video_id: str, text: str) -> dict[str, Any]:
        """Post a top-level comment on a video as the authenticated channel."""
        body = {
            "snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}
        }
        return client.request(
            "POST",
            "commentThreads",
            params={"part": "snippet"},
            json_body=body,
            op="commentThreads.insert",
        )

    @mcp.tool(title="Reply to a comment", annotations=WRITE)
    def youtube_reply_to_comment(parent_id: str, text: str) -> dict[str, Any]:
        """Reply to a top-level comment."""
        body = {"snippet": {"parentId": parent_id, "textOriginal": text}}
        return client.request(
            "POST", "comments", params={"part": "snippet"}, json_body=body, op="comments.insert"
        )

    @mcp.tool(title="Edit a comment", annotations=WRITE)
    def youtube_update_comment(comment_id: str, text: str) -> dict[str, Any]:
        """Edit the text of one of your comments."""
        body = {"id": comment_id, "snippet": {"textOriginal": text}}
        return client.request("PUT", "comments", params={"part": "snippet"}, json_body=body)

    @mcp.tool(title="Moderate comments", annotations=WRITE)
    def youtube_set_comment_moderation_status(
        comment_ids: list[str], moderation_status: str, ban_author: bool = False
    ) -> dict[str, Any]:
        """Moderate comments on your videos. moderation_status: published | heldForReview |
        rejected. ban_author (only with rejected) hides the author's future comments."""
        return client.request(
            "POST",
            "comments/setModerationStatus",
            params={
                "id": comment_ids,
                "moderationStatus": moderation_status,
                "banAuthor": ban_author if moderation_status == "rejected" else None,
            },
        )

    @mcp.tool(title="Mark comments as spam", annotations=WRITE)
    def youtube_mark_comments_as_spam(comment_ids: list[str]) -> dict[str, Any]:
        """Flag comments as spam."""
        return client.request("POST", "comments/markAsSpam", params={"id": comment_ids})

    @mcp.tool(title="Delete a comment", annotations=DESTRUCTIVE)
    def youtube_delete_comment(comment_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete one of your comments. Requires confirm=true."""
        require_confirm(confirm, "Deleting a comment")
        return client.request("DELETE", "comments", params={"id": comment_id})
