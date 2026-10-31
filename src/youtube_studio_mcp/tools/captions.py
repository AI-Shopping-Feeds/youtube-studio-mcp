"""Caption tracks: list, upload, update, download, delete."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..client import YouTubeClient
from ..media import guess_mime
from ._common import DESTRUCTIVE, READ, WRITE, require_confirm

MAX_INLINE_CHARS = 100_000


def register(mcp, client: YouTubeClient) -> None:
    @mcp.tool(title="List caption tracks", annotations=READ)
    def youtube_list_captions(video_id: str) -> dict[str, Any]:
        """List a video's caption tracks (language, name, kind, draft status). 50 quota units."""
        return client.request("GET", "captions", params={"part": "snippet", "videoId": video_id})

    @mcp.tool(title="Upload a caption track", annotations=WRITE)
    def youtube_upload_caption(
        video_id: str,
        source: str,
        language: str,
        name: str = "",
        is_draft: bool = False,
        sync: bool = False,
    ) -> dict[str, Any]:
        """Upload a caption track from a local file or URL (SRT, VTT, SBV, SCC...).

        language: BCP-47 code such as en or en-GB. sync=true lets YouTube re-time a plain
        transcript to the audio. 400 quota units.
        """
        body = {
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": name,
                "isDraft": is_draft,
            }
        }
        with client.media(source) as path:
            return client.upload(
                "captions",
                file_path=path,
                mime_type=guess_mime(path),
                params={"part": "snippet", "sync": sync or None},
                metadata=body,
                op="captions.insert",
            )

    @mcp.tool(title="Update a caption track", annotations=WRITE)
    def youtube_update_caption(
        caption_id: str,
        is_draft: bool | None = None,
        source: str | None = None,
        sync: bool = False,
    ) -> dict[str, Any]:
        """Publish/unpublish a caption track (is_draft) and/or replace its file (source)."""
        snippet = {} if is_draft is None else {"isDraft": is_draft}
        body: dict[str, Any] = {"id": caption_id, "snippet": snippet}
        params = {"part": "snippet", "sync": sync or None}
        if source is None:
            return client.request("PUT", "captions", params=params, json_body=body)
        with client.media(source) as path:
            return client.upload(
                "captions",
                method="PUT",
                file_path=path,
                mime_type=guess_mime(path),
                params=params,
                metadata=body,
                op="captions.update",
            )

    @mcp.tool(title="Download a caption track", annotations=READ)
    def youtube_download_caption(
        caption_id: str,
        tfmt: str | None = "srt",
        tlang: str | None = None,
        save_to: str | None = None,
    ) -> dict[str, Any]:
        """Download a caption track you own. tfmt: sbv | scc | srt | ttml | vtt. tlang
        machine-translates it. save_to writes the file to a local path instead of returning
        the text. 200 quota units."""
        data = client.download(f"captions/{caption_id}", params={"tfmt": tfmt, "tlang": tlang})
        if save_to:
            path = Path(save_to).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return {"saved_to": str(path.resolve()), "bytes": len(data)}
        text = data.decode("utf-8", errors="replace")
        return {
            "bytes": len(data),
            "truncated": len(text) > MAX_INLINE_CHARS,
            "text": text[:MAX_INLINE_CHARS],
        }

    @mcp.tool(title="Delete a caption track", annotations=DESTRUCTIVE)
    def youtube_delete_caption(caption_id: str, confirm: bool = False) -> dict[str, Any]:
        """Delete a caption track. Requires confirm=true."""
        require_confirm(confirm, "Deleting a caption track")
        return client.request("DELETE", "captions", params={"id": caption_id})
