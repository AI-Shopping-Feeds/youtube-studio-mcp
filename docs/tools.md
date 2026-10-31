# Tools

107 tools. Run `youtube-studio-mcp tools` to list them from your install.

Kind: **R** read, **W** write, **D** destructive (deletes need `confirm=true`).

## Server and auth

| Tool | Kind | What it does |
|---|---|---|
| `youtube_auth_status` | R | Show whether OAuth credentials exist, which scopes were granted and how to sign in. |
| `youtube_describe_server` | R | Show the server version, config, dry-run state and audit log location. |
| `youtube_set_dry_run` | W | Turn dry-run on or off for this session. In dry-run, writes and uploads are logged to the audit log but not sent to YouTube. |
| `youtube_audit_tail` | R | Show the most recent write operations from the audit log. |
| `youtube_audit_lookup` | R | Look up one audit log entry by ID. |

## Channels, sections, branding and subscriptions

| Tool | Kind | What it does |
|---|---|---|
| `youtube_channel_overview` | R | Get the authenticated channel: profile, branding, statistics and uploads playlist ID. |
| `youtube_list_channels` | R | List channels by ID, handle (e.g. "@GoogleDevelopers"), username, or your own (mine=true). Costs 1 quota unit. |
| `youtube_update_channel` | W | Update a channel resource (channels.update). `channel` must include `id`. |
| `youtube_upload_channel_banner` | W | Upload a channel banner image (local path or URL; 16:9, at least 2048x1152, max 6 MB). |
| `youtube_set_watermark` | W | Set the channel's video watermark (branding image) from a local path or URL. |
| `youtube_unset_watermark` | D | Remove the channel's video watermark. |
| `youtube_list_channel_sections` | R | List the shelves on a channel's home tab. |
| `youtube_create_channel_section` | W | Add a channel section. Example: {"snippet": {"type": "multiplePlaylists", "title": "Ads", "position": 1}, "contentDetails": {"playlists": ["PL..."]}}. |
| `youtube_update_channel_section` | W | Update a channel section. `section` must include `id`. |
| `youtube_delete_channel_section` | D | Delete a channel section. Requires confirm=true. |
| `youtube_list_activities` | R | List channel activity (uploads, likes, playlist additions...). Dates are RFC 3339. |
| `youtube_list_subscriptions` | R | List subscriptions: channels you subscribe to (mine), your recent subscribers (my_subscribers=true), or a channel's public subscriptions. order: alphabetical / relevance / unread. |
| `youtube_subscribe` | W | Subscribe the authenticated channel to another channel. |
| `youtube_unsubscribe` | D | Delete a subscription (use the subscription ID, not the channel ID). Requires confirm. |

## Videos, thumbnails and reference data

| Tool | Kind | What it does |
|---|---|---|
| `youtube_list_videos` | R | List your channel's uploads, newest first, with metadata, status and statistics. Includes private, unlisted and scheduled videos. |
| `youtube_get_video` | R | Get one video. For your own videos you can add fileDetails, processingDetails, suggestions, recordingDetails, localizations, paidProductPlacementDetails to `part`. |
| `youtube_videos_list` | R | videos.list: fetch up to 50 videos by ID, the mostPopular chart, or videos you rated (my_rating=like/dislike). 1 quota unit. |
| `youtube_batch_get_video_stats` | R | Get statistics for many videos at once (videos:batchGetStats, own 10,000/day bucket). |
| `youtube_update_video` | W | Update a video's title, description, tags, category, languages and status. |
| `youtube_update_video_resource` | W | Raw videos.update for fields youtube_update_video doesn't cover (recordingDetails, localizations, paidProductPlacementDetails...). `video` must include `id`; each part you send is replaced in full. |
| `youtube_delete_video` | D | Permanently delete one of your videos. Requires confirm=true. |
| `youtube_rate_video` | W | Like, dislike or clear your rating on a video. rating: like / dislike / none. |
| `youtube_get_video_rating` | R | Get your rating (like/dislike/none) for up to 50 videos. |
| `youtube_report_video_abuse` | W | Report a video for abuse. Get reason IDs from youtube_list_video_abuse_reasons. |
| `youtube_get_video_trainability` | R | Show which third parties a video's owner allows to train AI models on it. |
| `youtube_upload_thumbnail` | W | Set a custom thumbnail from a local image path or URL (JPEG/PNG, max 50 MB, 1280x720 recommended). The channel must be verified for custom thumbnails. |
| `youtube_list_video_categories` | R | List video category IDs (e.g. 22 People & Blogs, 26 Howto & Style) for a region. |
| `youtube_list_video_abuse_reasons` | R | List the reasons accepted by youtube_report_video_abuse. |
| `youtube_list_languages` | R | List the interface languages YouTube supports (i18nLanguages). |
| `youtube_list_regions` | R | List the content regions YouTube supports (i18nRegions). |

## Video uploads

| Tool | Kind | What it does |
|---|---|---|
| `youtube_upload_video` | W | Upload a video to the authenticated YouTube channel (resumable, any size up to 256 GB). |
| `youtube_upload_videos` | W | Bulk-upload videos one after another. Each item takes the same keys as youtube_upload_video: {"source", "title", "description", "tags", "category_id", "privacy_status", "publish_at", "made_for_kids", "contains_synthetic_media", "has_paid_product_placement", "default_language", "default_audio_language", "notify_subscribers", "thumbnail", "playlist_ids", ...}. |
| `youtube_get_upload_status` | R | Check processing for uploaded videos: uploadStatus (uploaded/processed/rejected/failed), failure or rejection reason, privacy, processing progress and YouTube's suggestions. |

## Playlists

| Tool | Kind | What it does |
|---|---|---|
| `youtube_list_playlists` | R | List your playlists (default), a channel's playlists, or playlists by ID. |
| `youtube_create_playlist` | W | Create a playlist. privacy_status: public / unlisted / private. |
| `youtube_update_playlist` | W | Update a playlist resource. Include `id` and the full parts you change (e.g. snippet with title, status with privacyStatus). |
| `youtube_delete_playlist` | D | Delete a playlist (the videos stay). Requires confirm=true. |
| `youtube_list_playlist_items` | R | List the videos in a playlist. Raise max_pages to read more than 50. |
| `youtube_add_to_playlist` | W | Add videos to a playlist, in order. position: 0-based insert point (manual-sort playlists only). |
| `youtube_update_playlist_item` | W | Update a playlist item (e.g. move it: snippet.position, or contentDetails.note). Include `id` and the full snippet (playlistId and resourceId are required). |
| `youtube_remove_playlist_item` | D | Remove an item from a playlist (playlist item ID, not video ID). Requires confirm. |
| `youtube_list_playlist_images` | R | List a playlist's custom cover images. |
| `youtube_set_playlist_image` | W | Upload a playlist cover image (local path or URL, JPEG/PNG, max 50 MB). Pass playlist_image_id to replace an existing image instead of adding one. |
| `youtube_delete_playlist_image` | D | Delete a playlist cover image. Requires confirm=true. |

## Comments

| Tool | Kind | What it does |
|---|---|---|
| `youtube_list_comments` | R | List top-level comment threads (with replies) on a video, or across a channel. |
| `youtube_list_comment_replies` | R | List replies to a top-level comment. |
| `youtube_post_comment` | W | Post a top-level comment on a video as the authenticated channel. |
| `youtube_reply_to_comment` | W | Reply to a top-level comment. |
| `youtube_update_comment` | W | Edit the text of one of your comments. |
| `youtube_set_comment_moderation_status` | W | Moderate comments on your videos. moderation_status: published / heldForReview / rejected. ban_author (only with rejected) hides the author's future comments. |
| `youtube_mark_comments_as_spam` | W | Flag comments as spam. |
| `youtube_delete_comment` | D | Delete one of your comments. Requires confirm=true. |

## Captions

| Tool | Kind | What it does |
|---|---|---|
| `youtube_list_captions` | R | List a video's caption tracks (language, name, kind, draft status). 50 quota units. |
| `youtube_upload_caption` | W | Upload a caption track from a local file or URL (SRT, VTT, SBV, SCC...). |
| `youtube_update_caption` | W | Publish/unpublish a caption track (is_draft) and/or replace its file (source). |
| `youtube_download_caption` | R | Download a caption track you own. tfmt: sbv / scc / srt / ttml / vtt. tlang machine-translates it. save_to writes the file to a local path instead of returning the text. 200 quota units. |
| `youtube_delete_caption` | D | Delete a caption track. Requires confirm=true. |

## Search, memberships, Super Chat and links

| Tool | Kind | What it does |
|---|---|---|
| `youtube_search` | R | Search YouTube for videos, channels or playlists (search.list). |
| `youtube_list_members` | R | List channel members (memberships). Needs the memberships scope: `youtube-studio-mcp auth-init --extra-scope memberships`. |
| `youtube_list_membership_levels` | R | List the channel's membership levels (needs the memberships scope). |
| `youtube_list_super_chat_events` | R | List Super Chat and Super Sticker events from the channel's live streams (last 30 days). |
| `youtube_list_third_party_links` | R | List the channel's links to third parties, such as a linked merchant store (type: channelToStoreLink / channelToAffiliateProgramLink). |
| `youtube_upsert_third_party_link` | W | Create (or with update=true, update) a third-party link resource, e.g. a channel-to-store link. See the thirdPartyLinks reference for the body shape. |
| `youtube_delete_third_party_link` | D | Remove a third-party link. Requires confirm=true. |
| `youtube_report_abuse` | W | File an abuse report against any YouTube entity (abuseReports.insert). Body: {"snippet": {"subject": {"id": "...", "type": "..."}, "abuseTypes": [...], "description": "..."}}. |

## Live streaming

| Tool | Kind | What it does |
|---|---|---|
| `youtube_list_live_broadcasts` | R | List your live broadcasts. broadcast_status: active / all / completed / upcoming. |
| `youtube_create_live_broadcast` | W | Schedule a live broadcast (times are RFC 3339). Bind it to a stream with youtube_bind_live_broadcast, then go live with youtube_transition_live_broadcast. |
| `youtube_update_live_broadcast` | W | Update a live broadcast resource. Include `id` and the full parts you change. |
| `youtube_bind_live_broadcast` | W | Bind a broadcast to a live stream (omit stream_id to unbind). |
| `youtube_transition_live_broadcast` | W | Change a broadcast's state. broadcast_status: testing / live / complete. |
| `youtube_insert_cuepoint` | W | Insert an ad break (cuepoint) into a live broadcast. |
| `youtube_delete_live_broadcast` | D | Delete a broadcast. Requires confirm=true. |
| `youtube_list_live_streams` | R | List your live streams (ingestion settings, stream keys and health). |
| `youtube_create_live_stream` | W | Create a live stream (returns the ingestion address and stream key). |
| `youtube_update_live_stream` | W | Update a live stream resource. Include `id` and the full parts you change. |
| `youtube_delete_live_stream` | D | Delete a live stream. Requires confirm=true. |
| `youtube_list_live_chat_messages` | R | Read a live chat (liveChatId is on the broadcast's snippet). Poll again with nextPageToken after pollingIntervalMillis. |
| `youtube_post_live_chat_message` | W | Post a text message to a live chat. |
| `youtube_delete_live_chat_message` | D | Delete a live chat message. Requires confirm=true. |
| `youtube_close_live_chat_poll` | W | Close a live chat poll (liveChatMessages.transition, status=closed). |
| `youtube_list_live_chat_moderators` | R | List a live chat's moderators. |
| `youtube_add_live_chat_moderator` | W | Make a channel a moderator of a live chat. |
| `youtube_remove_live_chat_moderator` | D | Remove a live chat moderator. Requires confirm=true. |
| `youtube_ban_live_chat_user` | W | Ban a user from a live chat: permanently, or temporarily with ban_duration_seconds. |
| `youtube_unban_live_chat_user` | W | Lift a live chat ban (use the ban ID returned by youtube_ban_live_chat_user). |

## Analytics and bulk reports

| Tool | Kind | What it does |
|---|---|---|
| `youtube_channel_analytics` | R | Channel totals for a date range (YYYY-MM-DD): views, watch time, retention, engagement and subscribers. |
| `youtube_video_analytics` | R | Daily analytics for one video over a date range (YYYY-MM-DD). |
| `youtube_analytics_query` | R | Run any YouTube Analytics report (reports.query). |
| `youtube_list_analytics_groups` | R | List your Analytics groups (custom collections of videos, playlists or channels). |
| `youtube_create_analytics_group` | W | Create an Analytics group. item_type: youtube#video / youtube#playlist / youtube#channel / youtubePartner#asset. |
| `youtube_rename_analytics_group` | W | Rename an Analytics group. |
| `youtube_delete_analytics_group` | D | Delete an Analytics group. Requires confirm=true. |
| `youtube_list_analytics_group_items` | R | List the items in an Analytics group. |
| `youtube_add_analytics_group_items` | W | Add videos (or playlists/channels, via kind) to an Analytics group. |
| `youtube_remove_analytics_group_item` | D | Remove an item from an Analytics group. Requires confirm=true. |
| `youtube_list_report_types` | R | List bulk report types you can schedule with the Reporting API (e.g. channel_basic_a2). |
| `youtube_list_reporting_jobs` | R | List your scheduled Reporting API jobs. |
| `youtube_create_reporting_job` | W | Schedule a daily bulk report. The first reports appear within about 48 hours. |
| `youtube_delete_reporting_job` | D | Delete a reporting job. Requires confirm=true. |
| `youtube_list_reports` | R | List the reports a job has produced, with their download URLs. |
| `youtube_download_report` | R | Download a Reporting API report (CSV) by its downloadUrl. save_to writes it to a local file; otherwise the CSV text is returned (truncated if very large). |

## Any other API method

| Tool | Kind | What it does |
|---|---|---|
| `youtube_call_api` | D | Call any YouTube API REST method that has no dedicated tool. No media uploads. |
