---
name: posthog-session-replay
description: Create Session Replay playlists/filters in PostHog via API. Use when the user wants to create, update, or manage Session Replay filters/playlists in PostHog, such as filtering recordings by person properties (li_fat_id, utm_source), events, URLs, or other criteria. Triggers on requests like "create a session replay filter", "filter recordings by X", "make a playlist for Y visitors". (user)
---

# PostHog Session Replay Filters

Create Session Replay playlists with custom filters via PostHog API.

## Before Using This Skill

**ASK THE USER** for these required values before making any API calls:

1. **PostHog Personal API Key** (starts with `phx_`)
   - Get it at: https://us.posthog.com/settings/user-api-keys (US) or https://eu.posthog.com/settings/user-api-keys (EU)

2. **Project ID** (numeric)
   - Find at: PostHog → Settings → Project → Project ID

3. **Host** (default: `us.posthog.com`)
   - US: `us.posthog.com`
   - EU: `eu.posthog.com`

**Do NOT proceed without these values. Each user has their own API key.**

## Quick Start

Create a playlist with filters using curl:

```bash
curl -X POST "https://us.posthog.com/api/projects/{PROJECT_ID}/session_recording_playlists/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {API_KEY}" \
  -d '{
    "name": "Playlist Name",
    "description": "Description",
    "type": "filters",
    "filters": {
      "order": "start_time",
      "date_from": "-90d",
      "duration": [{"key": "active_seconds", "type": "recording", "value": 5, "operator": "gt"}],
      "filter_group": {
        "type": "AND",
        "values": [
          {
            "type": "AND",
            "values": [
              // Add filters here
            ]
          }
        ]
      },
      "order_direction": "DESC",
      "filter_test_accounts": false
    }
  }'
```

## Filter Types

### Person Property Filter

Filter by person properties (e.g., `li_fat_id`, `utm_source`, `email`):

```json
{
  "key": "li_fat_id",
  "type": "person",
  "operator": "is_set",
  "value": "is_set"
}
```

Operators: `is_set`, `is_not_set`, `exact`, `icontains`, `regex`

### Event Filter with Properties

Filter by events and their properties:

```json
{
  "id": "$pageview",
  "name": "$pageview",
  "type": "events",
  "properties": [
    {
      "key": "$host",
      "type": "event",
      "value": ["example.com", "www.example.com"],
      "operator": "exact"
    }
  ]
}
```

### URL Filter

Filter by current URL:

```json
{
  "id": "$pageview",
  "name": "$pageview",
  "type": "events",
  "properties": [
    {
      "key": "$current_url",
      "type": "event",
      "value": "https://example.com/checkout",
      "operator": "icontains"
    }
  ]
}
```

### Recording Property Filter

Filter by recording properties (device type, duration):

```json
{
  "key": "snapshot_source",
  "type": "recording",
  "value": ["mobile"],
  "operator": "exact"
}
```

### Log Entry Filter (Console Errors)

Filter by console logs:

```json
{
  "key": "level",
  "type": "log_entry",
  "value": ["error"],
  "operator": "exact"
}
```

## Common Filter Combinations

### LinkedIn Ad Visitors

```json
{
  "type": "AND",
  "values": [
    {"key": "li_fat_id", "type": "person", "operator": "is_set", "value": "is_set"},
    {
      "id": "$pageview",
      "name": "$pageview",
      "type": "events",
      "properties": [
        {"key": "$host", "type": "event", "value": ["thelai.com", "www.thelai.com"], "operator": "exact"}
      ]
    }
  ]
}
```

### Google Ads Visitors

```json
{
  "type": "AND",
  "values": [
    {"key": "$initial_utm_source", "type": "person", "value": ["google"], "operator": "exact"}
  ]
}
```

### Rage Clicks

```json
{
  "type": "AND",
  "values": [
    {"id": "$rageclick", "type": "events", "order": 0}
  ]
}
```

### Mobile Device Recordings

```json
{
  "type": "AND",
  "values": [
    {"key": "snapshot_source", "type": "recording", "value": ["mobile"], "operator": "exact"}
  ]
}
```

## API Operations

### List Playlists

```bash
curl -X GET "https://us.posthog.com/api/projects/{PROJECT_ID}/session_recording_playlists/" \
  -H "Authorization: Bearer {API_KEY}"
```

### Get Playlist

```bash
curl -X GET "https://us.posthog.com/api/projects/{PROJECT_ID}/session_recording_playlists/{PLAYLIST_ID}/" \
  -H "Authorization: Bearer {API_KEY}"
```

### Update Playlist

```bash
curl -X PATCH "https://us.posthog.com/api/projects/{PROJECT_ID}/session_recording_playlists/{PLAYLIST_ID}/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {API_KEY}" \
  -d '{"name": "Updated Name", "filters": {...}}'
```

### Delete Playlist

```bash
curl -X DELETE "https://us.posthog.com/api/projects/{PROJECT_ID}/session_recording_playlists/{PLAYLIST_ID}/" \
  -H "Authorization: Bearer {API_KEY}"
```

## Response Format

Successful creation returns:

```json
{
  "id": 949284,
  "short_id": "RP2NYX8l",
  "name": "Playlist Name",
  "type": "filters",
  "filters": {...}
}
```

The `short_id` is used in the UI URL: `https://us.posthog.com/project/{PROJECT_ID}/replay/playlists/{SHORT_ID}`

## Notes

- `type` must be `"filters"` for filter-based playlists (not `"collection"`)
- `filter_group` structure requires nested `type: "AND"` objects
- Date formats: `-90d`, `-30d`, `-7d`, `-1d` or ISO timestamps
- Common hosts: `us.posthog.com` (US), `eu.posthog.com` (EU)
