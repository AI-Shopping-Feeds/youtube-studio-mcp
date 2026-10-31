"""Generic escape hatch for any YouTube Data, Analytics or Reporting API method."""

from __future__ import annotations

from typing import Any

from ..client import API_BASES, YouTubeClient
from ._common import DESTRUCTIVE, require_confirm


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(annotations=DESTRUCTIVE)
    def youtube_call_api(
        http_method: str,
        path: str,
        api: str = "data",
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        confirm: bool = False,
    ) -> dict[str, Any]:
        """Call any YouTube API REST method that has no dedicated tool. No media uploads.

        api: data (youtube/v3) | analytics (youtubeAnalytics v2) | reporting (youtubereporting v1).
        path is relative to the API root, e.g. "videos", "liveBroadcasts/transition",
        "jobs/123/reports". params are query parameters (lists are comma-joined).
        Writes go through dry-run and the audit log; DELETE requires confirm=true.
        """
        if api not in API_BASES:
            raise ValueError(f"api must be one of {sorted(API_BASES)}.")
        if path.startswith(("http://", "https://")):
            raise ValueError("path must be relative to the API root, not a full URL.")
        method = http_method.upper()
        if method == "DELETE":
            require_confirm(confirm, "A DELETE call")
        return client.request(
            method,
            path,
            api=api,
            params=params,
            json_body=body,
            op=f"call_api {api} {method} {path}",
        )
