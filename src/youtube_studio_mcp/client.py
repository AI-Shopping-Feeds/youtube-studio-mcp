"""HTTP client for the YouTube Data, Analytics and Reporting APIs.

Handles auth, retries, paging, dry-run, the audit log and resumable media
uploads (videos, captions, thumbnails, banners, watermarks, playlist images).
"""

from __future__ import annotations

import json
import random
import re
import time
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import httpx

from . import __version__
from ._logging import get_logger
from .audit import AuditLog
from .config import Config
from .media import local_file

API_BASES = {
    "data": "https://youtube.googleapis.com/youtube/v3",
    "analytics": "https://youtubeanalytics.googleapis.com/v2",
    "reporting": "https://youtubereporting.googleapis.com/v1",
}
UPLOAD_BASE = "https://www.googleapis.com/upload/youtube/v3"
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
RETRYABLE_STATUSES = {500, 502, 503, 504}
MAX_ATTEMPTS = 5
# 403 reasons that a retry can't fix; everything quota-related lands here.
QUOTA_REASONS = {"quotaExceeded", "dailyLimitExceeded", "uploadLimitExceeded", "rateLimitExceeded"}

logger = get_logger("client")


class YouTubeAPIError(Exception):
    def __init__(self, status: int, body: Any, message: str = ""):
        self.status = status
        self.body = body
        self.reason = _error_reason(body)
        hint = ""
        if self.reason in QUOTA_REASONS:
            hint = (
                " (quota: videos.insert and search.list have their own daily buckets; "
                "request more via the YouTube API Services quota extension form)"
            )
        super().__init__(message or f"YouTube API error {status} {self.reason or ''}: {body}{hint}")


def _error_reason(body: Any) -> str | None:
    if not isinstance(body, dict):
        return None
    err = body.get("error")
    if not isinstance(err, dict):
        return None
    errors = err.get("errors") or []
    if errors and isinstance(errors[0], dict):
        return errors[0].get("reason")
    return err.get("status")


def clean_params(params: dict[str, Any] | None) -> dict[str, Any]:
    """Drop None values, join lists with commas and lower-case booleans."""
    out: dict[str, Any] = {}
    for key, value in (params or {}).items():
        if value is None:
            continue
        if isinstance(value, bool):
            out[key] = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            out[key] = ",".join(str(v) for v in value)
        else:
            out[key] = value
    return out


class YouTubeClient:
    def __init__(self, config: Config, auth: Any, audit: AuditLog):
        self.config = config
        self.auth = auth
        self.audit = audit
        self._http = httpx.Client(
            timeout=config.timeout,
            headers={"User-Agent": f"youtube-studio-mcp/{__version__}"},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._http.close()

    def media(self, source: str) -> AbstractContextManager[Path]:
        """Resolve a tool's path-or-URL argument to a local file (see media.local_file)."""
        return local_file(source, allowed_dir=self.config.upload_dir)

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.auth.access_token()}"}
        headers.update(extra or {})
        return headers

    def url(self, path: str, api: str = "data") -> str:
        if path.startswith("https://"):
            return path
        return f"{API_BASES[api]}/{path.lstrip('/')}"

    # ---- JSON requests -------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        api: str = "data",
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        op: str | None = None,
        read_only: bool = False,
    ) -> Any:
        """Send one API request and return parsed JSON ({} for empty responses)."""
        method = method.upper()
        url = self.url(path, api)
        query = clean_params(params)
        is_write = method in WRITE_METHODS and not read_only
        op = op or f"{method} {path}"

        if is_write and self.config.dry_run:
            audit_id = self.audit.record(
                op=op, method=method, url=url, params=query, request_body=json_body, dry_run=True
            )
            return {
                "_dry_run": True,
                "method": method,
                "url": url,
                "params": query,
                "body": json_body,
                "audit_id": audit_id,
            }

        resp = self._send(method, url, params=query, json=json_body)
        payload = self._payload(resp)
        if not resp.is_success:
            if is_write:
                self.audit.record(
                    op=op,
                    method=method,
                    url=url,
                    params=query,
                    request_body=json_body,
                    response_status=resp.status_code,
                    response_body=payload,
                    error=f"HTTP {resp.status_code}",
                )
            raise YouTubeAPIError(resp.status_code, payload)
        if is_write:
            audit_id = self.audit.record(
                op=op,
                method=method,
                url=url,
                params=query,
                request_body=json_body,
                response_status=resp.status_code,
                response_body=payload,
            )
            if isinstance(payload, dict):
                payload = {**payload, "_audit_id": audit_id}
            logger.info("write %s %s -> %d (audit=%s)", method, path, resp.status_code, audit_id)
        return payload

    def paginate(
        self,
        path: str,
        *,
        api: str = "data",
        params: dict[str, Any] | None = None,
        items_key: str = "items",
        max_pages: int | None = 1,
    ) -> dict[str, Any]:
        """Follow nextPageToken up to max_pages and merge the item lists."""
        params = dict(params or {})
        items: list[Any] = []
        pages = 0
        last: dict[str, Any] = {}
        while True:
            last = self.request("GET", path, api=api, params=params)
            items.extend(last.get(items_key, []) or [])
            pages += 1
            token = last.get("nextPageToken")
            if not token or (max_pages is not None and pages >= max_pages):
                break
            params["pageToken"] = token
        return {
            "count": len(items),
            items_key: items,
            "nextPageToken": last.get("nextPageToken"),
            "pageInfo": last.get("pageInfo"),
        }

    def download(
        self, path: str, *, api: str = "data", params: dict[str, Any] | None = None
    ) -> bytes:
        """GET a media resource (caption track, report file) and return its bytes."""
        resp = self._send("GET", self.url(path, api), params=clean_params(params))
        if not resp.is_success:
            raise YouTubeAPIError(resp.status_code, self._payload(resp))
        return resp.content

    # ---- resumable uploads ---------------------------------------------

    def upload(
        self,
        path: str,
        *,
        file_path: Path,
        mime_type: str,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        metadata: Any | None = None,
        op: str | None = None,
    ) -> Any:
        """Upload a local file with the resumable protocol and return the API response.

        The file is streamed in `config.upload_chunk_size` pieces, never loaded
        whole, and interrupted chunks are resumed from the byte the server
        last confirmed.
        """
        method = method.upper()
        url = f"{UPLOAD_BASE}/{path.lstrip('/')}"
        query = {**clean_params(params), "uploadType": "resumable"}
        size = file_path.stat().st_size
        op = op or f"upload {path}"
        media = {"file": str(file_path), "bytes": size, "mime_type": mime_type}

        if self.config.dry_run:
            audit_id = self.audit.record(
                op=op,
                method=method,
                url=url,
                params=query,
                request_body=metadata,
                media=media,
                dry_run=True,
            )
            return {
                "_dry_run": True,
                "method": method,
                "url": url,
                "params": query,
                "body": metadata,
                "media": media,
                "audit_id": audit_id,
            }

        try:
            session_url = self._start_session(method, url, query, metadata, mime_type, size)
            payload = self._send_chunks(session_url, file_path, size)
        except YouTubeAPIError as e:
            self.audit.record(
                op=op,
                method=method,
                url=url,
                params=query,
                request_body=metadata,
                media=media,
                response_status=e.status,
                response_body=e.body,
                error=str(e),
            )
            raise
        audit_id = self.audit.record(
            op=op,
            method=method,
            url=url,
            params=query,
            request_body=metadata,
            media=media,
            response_status=200,
            response_body=payload,
        )
        logger.info("upload %s %s (%d bytes, audit=%s)", path, file_path.name, size, audit_id)
        if isinstance(payload, dict):
            payload = {**payload, "_audit_id": audit_id}
        return payload

    def _start_session(
        self, method: str, url: str, query: dict[str, Any], metadata: Any, mime: str, size: int
    ) -> str:
        headers = {"X-Upload-Content-Type": mime, "X-Upload-Content-Length": str(size)}
        content = None
        if metadata is not None:
            headers["Content-Type"] = "application/json; charset=UTF-8"
            content = json.dumps(metadata).encode("utf-8")
        resp = self._send(method, url, params=query, content=content, extra_headers=headers)
        location = resp.headers.get("Location")
        if not resp.is_success or not location:
            raise YouTubeAPIError(resp.status_code, self._payload(resp))
        return location

    def _send_chunks(self, session_url: str, file_path: Path, size: int) -> Any:
        chunk = self.config.upload_chunk_size
        offset = 0
        failures = 0
        with file_path.open("rb") as f:
            while True:
                if size == 0:
                    headers = {"Content-Range": "bytes */0"}
                    data = b""
                else:
                    f.seek(offset)
                    data = f.read(min(chunk, size - offset))
                    end = offset + len(data) - 1
                    headers = {"Content-Range": f"bytes {offset}-{end}/{size}"}
                try:
                    resp = self._http.put(session_url, content=data, headers=self._headers(headers))
                except httpx.RequestError as e:
                    resp = None
                    logger.warning("upload chunk at %d failed: %s", offset, e)
                if resp is not None and resp.status_code in (200, 201):
                    return self._payload(resp)
                if resp is not None and resp.status_code == 308:
                    offset = _next_offset(resp)
                    failures = 0
                    continue
                if resp is not None and resp.status_code not in RETRYABLE_STATUSES:
                    raise YouTubeAPIError(resp.status_code, self._payload(resp))
                failures += 1
                if failures >= MAX_ATTEMPTS:
                    status = resp.status_code if resp is not None else 0
                    body = self._payload(resp) if resp is not None else "connection failed"
                    raise YouTubeAPIError(status, body, f"Upload failed after retries: {body}")
                _sleep_backoff(failures - 1)
                offset = self._query_offset(session_url, size)

    def _query_offset(self, session_url: str, size: int) -> int:
        """Ask the server how many bytes it has after an interrupted chunk."""
        try:
            resp = self._http.put(
                session_url,
                content=b"",
                headers=self._headers({"Content-Range": f"bytes */{size}"}),
            )
        except httpx.RequestError:
            return 0
        if resp.status_code == 308:
            return _next_offset(resp)
        return 0

    # ---- transport -----------------------------------------------------

    def _send(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        content: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                resp = self._http.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    content=content,
                    headers=self._headers(extra_headers),
                )
            except httpx.RequestError as e:
                last_exc = e
                logger.warning("transport error attempt=%d %s %s: %s", attempt + 1, method, url, e)
                _sleep_backoff(attempt)
                continue
            if resp.status_code in RETRYABLE_STATUSES and attempt < MAX_ATTEMPTS - 1:
                _sleep_backoff(attempt, resp)
                continue
            return resp
        raise YouTubeAPIError(0, str(last_exc), f"Request failed after retries: {last_exc}")

    @staticmethod
    def _payload(resp: httpx.Response) -> Any:
        if not resp.content:
            return {}
        try:
            return resp.json()
        except ValueError:
            return {"_raw": resp.text[:2000]}


def _next_offset(resp: httpx.Response) -> int:
    match = re.match(r"bytes=0-(\d+)", resp.headers.get("Range", ""))
    return int(match.group(1)) + 1 if match else 0


def _sleep_backoff(attempt: int, resp: httpx.Response | None = None) -> None:
    retry_after = 0.0
    if resp is not None and "Retry-After" in resp.headers:
        try:
            retry_after = float(resp.headers["Retry-After"])
        except ValueError:
            retry_after = 0.0
    time.sleep(max(retry_after, min(2**attempt, 30)) + random.uniform(0, 0.5))
