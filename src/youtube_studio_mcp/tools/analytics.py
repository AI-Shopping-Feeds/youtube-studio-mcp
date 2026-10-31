"""YouTube Analytics API v2 (reports, groups) and YouTube Reporting API v1 (bulk reports)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..client import YouTubeClient
from ._common import DESTRUCTIVE, READ, WRITE, require_confirm

DEFAULT_METRICS = (
    "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,"
    "likes,comments,shares,subscribersGained,subscribersLost"
)
MAX_INLINE_CHARS = 200_000


def register(mcp, client: YouTubeClient) -> None:
    def query(**params: Any) -> dict[str, Any]:
        return client.request("GET", "reports", api="analytics", params=params)

    @mcp.tool(title="Get channel analytics", annotations=READ)
    def youtube_channel_analytics(start_date: str, end_date: str) -> dict[str, Any]:
        """Channel totals for a date range (YYYY-MM-DD): views, watch time, retention,
        engagement and subscribers."""
        return query(
            ids="channel==MINE", startDate=start_date, endDate=end_date, metrics=DEFAULT_METRICS
        )

    @mcp.tool(title="Get video analytics", annotations=READ)
    def youtube_video_analytics(video_id: str, start_date: str, end_date: str) -> dict[str, Any]:
        """Daily analytics for one video over a date range (YYYY-MM-DD)."""
        return query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics=DEFAULT_METRICS,
            dimensions="day",
            filters=f"video=={video_id}",
            sort="day",
        )

    @mcp.tool(title="Run an analytics query", annotations=READ)
    def youtube_analytics_query(
        start_date: str,
        end_date: str,
        metrics: str = DEFAULT_METRICS,
        dimensions: str | None = None,
        filters: str | None = None,
        sort: str | None = None,
        max_results: int | None = None,
        start_index: int | None = None,
        ids: str = "channel==MINE",
        currency: str | None = None,
        include_historical_channel_data: bool | None = None,
    ) -> dict[str, Any]:
        """Run any YouTube Analytics report (reports.query).

        Examples: top videos: dimensions="video", sort="-views", max_results=10.
        Traffic sources: dimensions="insightTrafficSourceType". Geography: dimensions="country".
        Revenue metrics (estimatedRevenue, adImpressions, cpm) need the monetary scope and a
        monetised channel. Content owners use ids="contentOwner==OWNER_ID".
        """
        return query(
            ids=ids,
            startDate=start_date,
            endDate=end_date,
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            sort=sort,
            maxResults=max_results,
            startIndex=start_index,
            currency=currency,
            includeHistoricalChannelData=include_historical_channel_data,
        )

    @mcp.tool(title="List analytics groups", annotations=READ)
    def youtube_list_analytics_groups(
        id: list[str] | None = None, page_token: str | None = None
    ) -> dict[str, Any]:
        """List your Analytics groups (custom collections of videos, playlists or channels)."""
        return client.request(
            "GET",
            "groups",
            api="analytics",
            params={"mine": None if id else True, "id": id, "pageToken": page_token},
        )

    @mcp.tool(title="Create an analytics group", annotations=WRITE)
    def youtube_create_analytics_group(
        title: str, item_type: str = "youtube#video"
    ) -> dict[str, Any]:
        """Create an Analytics group. item_type: youtube#video | youtube#playlist |
        youtube#channel | youtubePartner#asset."""
        body = {"snippet": {"title": title}, "contentDetails": {"itemType": item_type}}
        return client.request("POST", "groups", api="analytics", json_body=body)

    @mcp.tool(title="Rename an analytics group", annotations=WRITE)
    def youtube_rename_analytics_group(group_id: str, title: str) -> dict[str, Any]:
        """Rename an Analytics group."""
        return client.request(
            "PUT",
            "groups",
            api="analytics",
            json_body={"id": group_id, "snippet": {"title": title}},
        )

    @mcp.tool(title="Delete an analytics group", annotations=DESTRUCTIVE)
    def youtube_delete_analytics_group(group_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete an Analytics group. Requires confirm=true."""
        require_confirm(confirm, "Deleting an Analytics group")
        return client.request("DELETE", "groups", api="analytics", params={"id": group_id})

    @mcp.tool(title="List analytics group items", annotations=READ)
    def youtube_list_analytics_group_items(group_id: str) -> dict[str, Any]:
        """List the items in an Analytics group."""
        return client.request("GET", "groupItems", api="analytics", params={"groupId": group_id})

    @mcp.tool(title="Add items to an analytics group", annotations=WRITE)
    def youtube_add_analytics_group_items(
        group_id: str, resource_ids: list[str], kind: str = "youtube#video"
    ) -> dict[str, Any]:
        """Add videos (or playlists/channels, via kind) to an Analytics group."""
        added = [
            client.request(
                "POST",
                "groupItems",
                api="analytics",
                json_body={"groupId": group_id, "resource": {"kind": kind, "id": rid}},
            )
            for rid in resource_ids
        ]
        return {"added": len(added), "items": added}

    @mcp.tool(title="Remove an analytics group item", annotations=DESTRUCTIVE)
    def youtube_remove_analytics_group_item(
        group_item_id: str, confirm: bool = False
    ) -> dict[str, Any]:
        """Remove an item from an Analytics group. Requires confirm=true."""
        require_confirm(confirm, "Removing a group item")
        return client.request("DELETE", "groupItems", api="analytics", params={"id": group_item_id})

    # ---- Reporting API (scheduled bulk CSV reports) ----

    @mcp.tool(title="List report types", annotations=READ)
    def youtube_list_report_types(include_system_managed: bool | None = None) -> dict[str, Any]:
        """List bulk report types you can schedule with the Reporting API (e.g. channel_basic_a2)."""
        return client.request(
            "GET",
            "reportTypes",
            api="reporting",
            params={"includeSystemManaged": include_system_managed},
        )

    @mcp.tool(title="List reporting jobs", annotations=READ)
    def youtube_list_reporting_jobs(include_system_managed: bool | None = None) -> dict[str, Any]:
        """List your scheduled Reporting API jobs."""
        return client.request(
            "GET", "jobs", api="reporting", params={"includeSystemManaged": include_system_managed}
        )

    @mcp.tool(title="Create a reporting job", annotations=WRITE)
    def youtube_create_reporting_job(report_type_id: str, name: str) -> dict[str, Any]:
        """Schedule a daily bulk report. The first reports appear within about 48 hours."""
        return client.request(
            "POST",
            "jobs",
            api="reporting",
            json_body={"reportTypeId": report_type_id, "name": name},
        )

    @mcp.tool(title="Delete a reporting job", annotations=DESTRUCTIVE)
    def youtube_delete_reporting_job(job_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a reporting job. Requires confirm=true."""
        require_confirm(confirm, "Deleting a reporting job")
        return client.request("DELETE", f"jobs/{job_id}", api="reporting")

    @mcp.tool(title="List generated reports", annotations=READ)
    def youtube_list_reports(
        job_id: str,
        created_after: str | None = None,
        start_time_at_or_after: str | None = None,
        start_time_before: str | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List the reports a job has produced, with their download URLs."""
        return client.request(
            "GET",
            f"jobs/{job_id}/reports",
            api="reporting",
            params={
                "createdAfter": created_after,
                "startTimeAtOrAfter": start_time_at_or_after,
                "startTimeBefore": start_time_before,
                "pageToken": page_token,
            },
        )

    @mcp.tool(title="Download a report", annotations=READ)
    def youtube_download_report(download_url: str, save_to: str | None = None) -> dict[str, Any]:
        """Download a Reporting API report (CSV) by its downloadUrl. save_to writes it to a
        local file; otherwise the CSV text is returned (truncated if very large)."""
        if not download_url.startswith("https://youtubereporting.googleapis.com/"):
            raise ValueError("download_url must be a youtubereporting.googleapis.com URL.")
        data = client.download(download_url)
        if save_to:
            path = Path(save_to).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return {"saved_to": str(path.resolve()), "bytes": len(data)}
        text = data.decode("utf-8", errors="replace")
        return {
            "bytes": len(data),
            "truncated": len(text) > MAX_INLINE_CHARS,
            "csv": text[:MAX_INLINE_CHARS],
        }
