"""OAuth user credentials for the YouTube APIs.

YouTube channels can't be accessed with service accounts, so this server uses
an installed-app OAuth flow (`youtube-studio-mcp auth-init`) and stores the
refresh token in a local JSON file. Token files written by the original
`scripts/auth.py` (raw token response, no client ID) still load: the client ID
and secret are filled in from the client-secrets file.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

TOKEN_URI = "https://oauth2.googleapis.com/token"

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/yt-analytics-monetary.readonly",
]

# Only granted to channels with memberships / YouTube partners. Opt in with
# `auth-init --extra-scope`.
OPTIONAL_SCOPES = {
    "memberships": "https://www.googleapis.com/auth/youtube.channel-memberships.creator",
    "partner": "https://www.googleapis.com/auth/youtubepartner",
    "partner-channel-audit": "https://www.googleapis.com/auth/youtubepartner-channel-audit",
}


def load_client_info(client_secrets: Path) -> dict[str, Any]:
    data = json.loads(client_secrets.read_text(encoding="utf-8"))
    info = data.get("installed") or data.get("web") or data
    if "client_id" not in info:
        raise RuntimeError(f"{client_secrets} is not an OAuth client JSON (no client_id).")
    return info


class OAuthUserAuth:
    """Loads credentials lazily, refreshes them and writes refreshed tokens back."""

    def __init__(self, token_file: Path, client_secrets: Path):
        self.token_file = token_file
        self.client_secrets = client_secrets
        self._creds: Credentials | None = None
        self._lock = threading.Lock()

    @property
    def account_label(self) -> str:
        return f"oauth-user:{self.token_file.name}"

    def status(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "client_secrets": str(self.client_secrets),
            "client_secrets_exists": self.client_secrets.exists(),
            "token_file": str(self.token_file),
            "token_exists": self.token_file.exists(),
        }
        if self.token_file.exists():
            try:
                data = json.loads(self.token_file.read_text(encoding="utf-8"))
                scopes = data.get("scopes") or (data.get("scope") or "").split()
                info["granted_scopes"] = scopes
                info["has_refresh_token"] = bool(data.get("refresh_token"))
            except (OSError, ValueError) as e:
                info["token_error"] = str(e)
        return info

    def _load(self) -> Credentials:
        if not self.token_file.exists():
            raise RuntimeError(
                f"OAuth token not found at {self.token_file}. Run "
                "`youtube-studio-mcp auth-init --client-secrets path/to/client_secret.json`."
            )
        data = json.loads(self.token_file.read_text(encoding="utf-8"))
        if "client_id" not in data:
            if not self.client_secrets.exists():
                raise RuntimeError(
                    f"{self.token_file} has no client_id and the client-secrets file "
                    f"{self.client_secrets} is missing. Set YOUTUBE_CLIENT_SECRETS or re-run auth-init."
                )
            client = load_client_info(self.client_secrets)
            data = {
                **data,
                "client_id": client["client_id"],
                "client_secret": client.get("client_secret"),
                "token_uri": client.get("token_uri", TOKEN_URI),
            }
            if "scopes" not in data and data.get("scope"):
                data["scopes"] = data["scope"].split()
        if not data.get("refresh_token"):
            raise RuntimeError(f"{self.token_file} has no refresh_token. Re-run auth-init.")
        return Credentials.from_authorized_user_info(data)

    def access_token(self) -> str:
        with self._lock:
            if self._creds is None:
                self._creds = self._load()
            if not self._creds.valid:
                self._creds.refresh(Request())
                self.token_file.write_text(self._creds.to_json(), encoding="utf-8")
            return str(self._creds.token)
