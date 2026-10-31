# Google OAuth setup

YouTube Studio MCP signs in with your own Google Cloud OAuth client, so channel access
stays under your control. YouTube channels can't be reached with service accounts.

## 1. Create a Google Cloud project

Use a project dedicated to this server. Quota is counted per project.

## 2. Enable the APIs

In **APIs & Services → Library**, enable:

- YouTube Data API v3
- YouTube Analytics API
- YouTube Reporting API (only for the bulk report tools)

## 3. Configure the OAuth consent screen

An **External** app in **Testing** mode is enough for your own channels: add each Google
account that will sign in as a test user. Testing-mode refresh tokens expire after 7 days;
publish the app (and complete Google's verification for the YouTube scopes) for long-lived
tokens.

## 4. Create the OAuth client

**Credentials → Create credentials → OAuth client ID → Desktop app.** Download the JSON and
save it as `secrets/client_secret.json` (or anywhere, and point `YOUTUBE_CLIENT_SECRETS` at it).

## 5. Sign in

```bash
uvx --from git+https://github.com/AI-Shopping-Feeds/youtube-studio-mcp.git \
  youtube-studio-mcp auth-init --client-secrets secrets/client_secret.json --output secrets/token.json
```

A browser opens. Sign in with the Google account that owns or manages the channel. For a
Brand Account channel, pick the channel when Google asks. The token is saved to
`secrets/token.json` with owner-only permissions.

Add `--extra-scope memberships` to use the memberships tools, or `--extra-scope partner`
for YouTube content-owner (CMS) accounts.

## Scopes requested

| Scope | Used for |
|---|---|
| `youtube` | Manage the channel: videos, playlists, comments, live streams |
| `youtube.force-ssl` | Captions, comments and other SSL-only methods |
| `youtube.upload` | Video uploads |
| `youtube.readonly` | Read channel data |
| `yt-analytics.readonly` | YouTube Analytics and Reporting |
| `yt-analytics-monetary.readonly` | Revenue metrics (monetised channels) |

## Quota and the upload audit

- `videos.insert` and `search.list` each have their own daily bucket (default 100 calls a
  day per project). Everything else shares a 10,000-unit daily bucket: most reads cost 1
  unit and most writes 50. Request more with the
  [quota extension form](https://support.google.com/youtube/contact/yt_api_form).
- Google has required unaudited API projects' uploads to be locked to private since 2020.
  Its current `videos.insert` reference says they no longer are. Check the
  `privacyStatus` of your first upload; if it is locked, apply for the
  [API compliance audit](https://support.google.com/youtube/contact/yt_api_form).
