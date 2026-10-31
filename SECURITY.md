# Security

This server can upload, edit and delete videos, playlists, captions and comments, run
live streams and read analytics, using OAuth permissions granted by the channel owner.

## Protect your credentials

- Never commit `secrets/client_secret.json` or `secrets/token.json` (both are git-ignored).
- `auth-init` writes the token file with owner-only permissions. Keep it that way.
- Revoke access at https://myaccount.google.com/permissions if a machine is lost.
- Use a dedicated Google Cloud project for this server.
- Set `YOUTUBE_UPLOAD_DIR` so the agent can only upload files from one folder.

## Reporting issues

Open a private security advisory on GitHub, or contact the maintainers at
[AI Shopping Feeds](https://github.com/AI-Shopping-Feeds). Don't post working exploits or
leaked credentials in a public issue.
