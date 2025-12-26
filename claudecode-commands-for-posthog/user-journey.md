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

### Step 3: Get user profile and identifiers (INCLUDING person_id)

**If input is EMAIL**, run this query:
```sql
SELECT
    person_id,
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
GROUP BY person_id, email, ip, distinct_id, browser, browser_version, os, device, city, state, country
ORDER BY total_events DESC
LIMIT 1
```

**If input is IP**, run this query:
```sql
SELECT
    person_id,
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
GROUP BY person_id, email, ip, distinct_id, browser, browser_version, os, device, city, state, country
ORDER BY total_events DESC
LIMIT 1
```

**IMPORTANT**: Save these values for later:
- `person_id` → **PRIMARY KEY** - Will be used for ALL event queries to avoid data mixing
- `email` → For display and related users search
- `ip` → For finding related users only (NOT for event queries)
- `distinct_id` → Will be used for PostHog person link

---

### Step 4: Find Related Users (CRITICAL FOR SHARED IPs)

**ALWAYS** run this query to detect other users sharing the same IP:
```sql
SELECT DISTINCT
    person_id,
    person.properties.email as email,
    count() as total_events
FROM events
WHERE properties.$ip = '{IP_FROM_STEP_3}'
AND person.properties.email IS NOT NULL
AND person_id != '{PERSON_ID_FROM_STEP_3}'
GROUP BY person_id, email
ORDER BY total_events DESC
LIMIT 10
```

**If related users are found**, they will be displayed in a separate section at the end of the report.

---

### Step 5: Get traffic source (first pageview) - USE PERSON_ID

Use the **person_id** (NOT IP) to find the original traffic source:
```sql
SELECT
    properties.$referrer as referrer,
    properties.$referring_domain as referring_domain,
    properties.$utm_source as utm_source,
    properties.$utm_medium as utm_medium,
    properties.$utm_campaign as utm_campaign
FROM events
WHERE person_id = '{PERSON_ID_FROM_STEP_3}'
AND event = '$pageview'
ORDER BY timestamp ASC
LIMIT 1
```

**Traffic Source Logic**:
- If `utm_source` exists → Use it (e.g., "Google Ads", "LinkedIn")
- If `referring_domain` exists and is not `$direct` → Use it
- Otherwise → "Direct"

---

### Step 6: Get ALL events using PERSON_ID (NOT IP)

**CRITICAL**: Always use the **person_id** to search. This ensures we only get events for this specific user and avoids mixing data from users sharing the same IP (common in universities, offices, etc.)

```sql
SELECT
    event,
    properties.$current_url as url,
    properties.$host as domain,
    properties.$session_id as session_id,
    timestamp
FROM events
WHERE person_id = '{PERSON_ID_FROM_STEP_3}'
AND event IN ('$pageview', 'form_viewed', 'form_submitted_successfully', 'academic_form_conversion', 'form_conversion', '$exception', 'quote_requested', 'file_uploaded')
ORDER BY timestamp ASC
LIMIT 300
```

---

### Step 7: Get exception details (if any) - USE PERSON_ID

If there were `$exception` events, get the details:
```sql
SELECT
    timestamp,
    properties.$exception_type as type,
    properties.$exception_message as message,
    properties.$current_url as url
FROM events
WHERE person_id = '{PERSON_ID_FROM_STEP_3}'
AND event = '$exception'
ORDER BY timestamp DESC
LIMIT 5
```

---

### Step 8: Generate the report

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
| **PostHog Person** | [View in PostHog](https://us.posthog.com/project/142642/person/{distinct_id}) |

---

### Session {N}: {Month Day, Year} ({Start Time} - {End Time} {Timezone})

**{Phase Name}** ({domain})

| Time | Event | Page | PostHog Link |
|------|-------|------|--------------|
| {HH:MM:SS AM/PM} | {Event Name} | {Page Name} | [View Session](https://us.posthog.com/project/142642/replay/{session_id}) |

---

### Summary
- {Insight about user type: new lead, returning customer, academic, etc.}
- {Insight about traffic source}
- {Insight about conversion or key actions taken}
- {Insight about any errors encountered}

---

### Related Users Found (Same IP: {ip_address})

> **Note**: The following users share the same IP address. This is common in university/corporate networks. Their data is **NOT** included in the report above.

| Email | PostHog Person | Events |
|-------|----------------|--------|
| {related_email_1} | [View](https://us.posthog.com/project/142642/person/{related_distinct_id_1}) | {event_count_1} |
| {related_email_2} | [View](https://us.posthog.com/project/142642/person/{related_distinct_id_2}) | {event_count_2} |

*If no related users are found, omit this section entirely.*
```

---

## Mappings Reference

### Event Names
| PostHog Event | Display Name |
|---------------|--------------|
| `$pageview` | Pageview |
| `form_viewed` | Form Viewed |
| `form_submitted_successfully` | **Form Submitted** |
| `academic_form_conversion` | **Academic Conversion** |
| `form_conversion` | **Conversion** |
| `quote_requested` | **Quote Requested** |
| `file_uploaded` | File Uploaded |
| `$exception` | Error: {type} |

### Page Names (extract from URL path)
| URL Pattern | Display Name |
|-------------|--------------|
| `/` (root) | Homepage |
| `/transcription` | Transcription Page |
| `/our-customers` | Our Customers |
| `/pricing` | Pricing |
| `/contact` | Contact |
| `/about` | About |
| `/V3_Dashboard` | Dashboard |
| `/apex/V3_Dashboard` | Dashboard |
| `/apex/V3_Get_Quote` | Get Quote |
| `/apex/QuoteGenerator` | Quote Generator |
| `/apex/V3_User_Details` | User Details |
| `/apex/V3_Transcriptionist_*` | {Last segment cleaned} |
| `/apex/VF_*` | {Last segment cleaned} |
| Other | Use last path segment, replace underscores with spaces |

### Domain Labels
| Domain | Label |
|--------|-------|
| `www.thelai.com` | Website |
| `thelai.com` | Website |
| `landmarkassociates.my.salesforce-sites.com` | Salesforce Portal |
| `landmarkassociates--c.vf.force.com` | Salesforce Portal (Internal) |

### Session Grouping Rules
1. Group events by `session_id`
2. If `session_id` changes → new session
3. If same `session_id` but domain changes → label as new phase within session
4. If gap between events > 30 minutes → consider it a new session even if same ID

---

## Project Configuration
- **PostHog Project ID**: `142642`
- **PostHog Base URL**: `https://us.posthog.com`
- **Person Link**: `https://us.posthog.com/project/142642/person/{distinct_id}`
- **Session Replay Link**: `https://us.posthog.com/project/142642/replay/{session_id}`

---

## Why person_id instead of IP?

**Problem with IP-based queries:**
- Multiple users can share the same IP (universities, offices, VPNs)
- Data from different users gets mixed in the report
- Example: Yale University users share IP `128.36.x.x`

**Solution with person_id:**
- `person_id` is PostHog's unique identifier for each user
- Guaranteed to be unique per person
- No data mixing even if users share the same IP

**When to still use IP:**
- Only for the "Related Users Found" section
- To inform the user about other people on the same network
- Their data is NOT included in the main report
