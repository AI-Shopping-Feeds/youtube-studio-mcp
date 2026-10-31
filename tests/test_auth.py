from __future__ import annotations

import json

from youtube_studio_mcp.auth import OAuthUserAuth


def test_legacy_token_file_loads_with_client_secrets(tmp_path):
    secrets = tmp_path / "client_secret.json"
    secrets.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "cid",
                    "client_secret": "cs",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
        )
    )
    token = tmp_path / "token.json"
    # Shape written by the upstream scripts/auth.py: raw token response + created_at.
    token.write_text(
        json.dumps(
            {
                "access_token": "at",
                "refresh_token": "rt",
                "expires_in": 3599,
                "scope": "https://www.googleapis.com/auth/youtube",
                "token_type": "Bearer",
                "created_at": 1,
            }
        )
    )
    auth = OAuthUserAuth(token, secrets)
    creds = auth._load()
    assert creds.client_id == "cid"
    assert creds.refresh_token == "rt"
    assert auth.status()["granted_scopes"] == ["https://www.googleapis.com/auth/youtube"]


def test_missing_token_explains_auth_init(tmp_path):
    auth = OAuthUserAuth(tmp_path / "none.json", tmp_path / "cs.json")
    try:
        auth.access_token()
    except RuntimeError as e:
        assert "auth-init" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
