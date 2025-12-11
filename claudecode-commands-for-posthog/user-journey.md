# User Journey Tracker

Generate a complete cross-domain user journey report from PostHog.

---

## Instructions

Using the PostHog MCP tools (`mcp__posthog__query-run`), generate a complete user journey report. Follow these steps **exactly**:

### Step 1: Ask for email or IP

**ALWAYS** start by using the `AskUserQuestion` tool to ask:

```
Question: "Enter the email or IP address to search:"
Header: "User Journey"
Options:
  - Label: "Email", Description: "e.g. user@company.com"
  - Label: "IP Address", Description: "e.g. 192.168.1.100"
```

Wait for the user's response before continuing.

### Step 2: Detect input type
- If input contains `@` → it's an **email**
- Otherwise → it's an **IP address**

---

### Step 3: Get user profile and identifiers

**If input is EMAIL**, run this query:
```sql
SELECT
    person.properties.email as email,
    properties.$ip as ip,
    distinct_id,
    properties.$browser as browser,
    properties.$browser_version as browser_version,
    properties.$os as os,
    properties.$device_type as device,
    properties.$geoip_city_name as city,
    properties.$geoip_subdivision_1_name as state,
    properties.$geoip_country_name as country,
    min(timestamp) as first_seen,
    max(timestamp) as last_seen,
    count() as total_events
FROM events
WHERE person.properties.email = '{INPUT_EMAIL}'
GROUP BY email, ip, distinct_id, browser, browser_version, os, device, city, state, country
ORDER BY total_events DESC
LIMIT 1
```

**If input is IP**, run this query:
```sql
SELECT
    person.properties.email as email,
    properties.$ip as ip,
    distinct_id,
    properties.$browser as browser,
    properties.$browser_version as browser_version,
    properties.$os as os,
    properties.$device_type as device,
    properties.$geoip_city_name as city,
    properties.$geoip_subdivision_1_name as state,
    properties.$geoip_country_name as country,
    min(timestamp) as first_seen,
    max(timestamp) as last_seen,
    count() as total_events
FROM events
WHERE properties.$ip = '{INPUT_IP}'
GROUP BY email, ip, distinct_id, browser, browser_version, os, device, city, state, country
ORDER BY total_events DESC
LIMIT 1
```

**IMPORTANT**: Save these values for later:
- `email` → Will be used for searching
- `ip` → Will be used for cross-domain searching
- `distinct_id` → Will be used for PostHog person link

---

### Step 4: Get traffic source (first pageview)

Use the **IP** from Step 3 to find the original traffic source:
```sql
SELECT
    properties.$referrer as referrer,
    properties.$referring_domain as referring_domain,
    properties.$utm_source as utm_source,
    properties.$utm_medium as utm_medium,
    properties.$utm_campaign as utm_campaign
FROM events
WHERE properties.$ip = '{IP_FROM_STEP_3}'
AND event = '$pageview'
ORDER BY timestamp ASC
LIMIT 1
```

**Traffic Source Logic**:
- If `utm_source` exists → Use it (e.g., "Google Ads", "LinkedIn")
- If `referring_domain` exists and is not `$direct` → Use it
- Otherwise → "Direct"

---

### Step 5: Get ALL events across ALL domains using IP

**CRITICAL**: Always use the **IP address** to search. This captures activity across all domains.

```sql
SELECT
    event,
    properties.$current_url as url,
    properties.$host as domain,
    properties.$session_id as session_id,
    timestamp
FROM events
WHERE properties.$ip = '{IP_FROM_STEP_3}'
AND event IN ('$pageview', 'form_viewed', 'form_submitted_successfully', 'form_conversion', '$exception', 'quote_requested', 'file_uploaded')
ORDER BY timestamp ASC
LIMIT 300
```

---

### Step 6: Get exception details (if any)

If there were `$exception` events, get the details:
```sql
SELECT
    timestamp,
    properties.$exception_type as type,
    properties.$exception_message as message,
    properties.$current_url as url
FROM events
WHERE properties.$ip = '{IP_FROM_STEP_3}'
AND event = '$exception'
ORDER BY timestamp DESC
LIMIT 5
```

---

### Step 7: Generate the report

Use this exact format:

```markdown
## User Journey: {email OR ip}

### User Profile
| Field | Value |
|-------|-------|
| **Email** | {email or "Unknown"} |
| **Location** | {city}, {state}, {country} |
| **Browser** | {browser} {browser_version} |
| **OS** | {os} |
| **Device** | {device} |
| **Traffic Source** | {traffic_source} |
| **First Seen** | {first_seen date/time} |
| **Last Seen** | {last_seen date/time} |
| **PostHog Person** | [View in PostHog](https://us.posthog.com/project/{PROJECT_ID}/person/{distinct_id}) |

---

### Session {N}: {Month Day, Year} ({Start Time} - {End Time} {Timezone})

**{Phase Name}** ({domain})

| Time | Event | Page | PostHog Link |
|------|-------|------|--------------|
| {HH:MM:SS AM/PM} | {Event Name} | {Page Name} | [View Session](https://us.posthog.com/project/{PROJECT_ID}/replay/{session_id}) |

---

### Summary
- {Insight about user type: new lead, returning customer, etc.}
- {Insight about traffic source}
- {Insight about conversion or key actions taken}
- {Insight about any errors encountered}
```

---

## Mappings Reference

### Event Names
| PostHog Event | Display Name |
|---------------|--------------|
| `$pageview` | Pageview |
| `form_viewed` | Form Viewed |
| `form_submitted_successfully` | **Form Submitted** |
| `form_conversion` | **Conversion** |
| `quote_requested` | **Quote Requested** |
| `file_uploaded` | File Uploaded |
| `$exception` | Error: {type} |

### Page Names (extract from URL path)
| URL Pattern | Display Name |
|-------------|--------------|
| `/` (root) | Homepage |
| `/pricing` | Pricing |
| `/contact` | Contact |
| `/about` | About |
| Other | Use last path segment, replace underscores with spaces |

### Session Grouping Rules
1. Group events by `session_id`
2. If `session_id` changes → new session
3. If same `session_id` but domain changes → label as new phase within session
4. If gap between events > 30 minutes → consider it a new session even if same ID

---

## Configuration

Before using this command, update the following values in your copy:

| Variable | Description | Example |
|----------|-------------|---------|
| `{PROJECT_ID}` | Your PostHog project ID | `12345` |

You can find your Project ID in PostHog under **Settings > Project > Project ID**.

### PostHog URL Patterns
- **Person Link**: `https://us.posthog.com/project/{PROJECT_ID}/person/{distinct_id}`
- **Session Replay Link**: `https://us.posthog.com/project/{PROJECT_ID}/replay/{session_id}`

> **Note**: If you use EU hosting, replace `us.posthog.com` with `eu.posthog.com`
