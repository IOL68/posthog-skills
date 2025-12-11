# Claude Code Commands for PostHog

Custom slash commands for [Claude Code](https://claude.ai/code) that integrate with PostHog analytics.

## Available Commands

| Command | Description |
|---------|-------------|
| `/user-journey` | Generate a complete cross-domain user journey report |

---

## Installation

### Prerequisites

1. **Claude Code** installed and configured
2. **PostHog MCP Server** connected to Claude Code
   - You need the [PostHog MCP](https://github.com/PostHog/posthog-mcp) server configured

### Steps

1. **Create the commands directory** (if it doesn't exist):
   ```bash
   mkdir -p ~/.claude/commands
   ```

2. **Copy the command file**:
   ```bash
   cp user-journey.md ~/.claude/commands/
   ```

3. **Configure your Project ID**:

   Open `~/.claude/commands/user-journey.md` and replace `{PROJECT_ID}` with your actual PostHog project ID.

   You can find your Project ID in PostHog under **Settings > Project > Project ID**.

4. **Restart Claude Code** (or start a new conversation)

---

## Usage

### User Journey Command

Generate a complete user journey report by email or IP address:

```
/user-journey user@example.com
```

or

```
/user-journey 192.168.1.100
```

### What it does

1. **Identifies the user** from email or IP
2. **Gets user profile** (location, browser, device, etc.)
3. **Finds traffic source** (UTM parameters, referrer, or direct)
4. **Tracks cross-domain activity** using IP address
5. **Generates a formatted report** with:
   - User profile table
   - Session timeline with events
   - Direct links to PostHog session replays
   - Summary insights

### Example Output

```markdown
## User Journey: user@example.com

### User Profile
| Field | Value |
|-------|-------|
| **Email** | user@example.com |
| **Location** | New York, NY, United States |
| **Browser** | Chrome 120 |
| **OS** | Mac OS X |
| **Device** | Desktop |
| **Traffic Source** | Google Ads |
| **PostHog Person** | [View in PostHog](https://us.posthog.com/project/12345/person/abc123) |

---

### Session 1: December 10, 2025 (2:30 PM - 2:45 PM EST)

| Time | Event | Page | PostHog Link |
|------|-------|------|--------------|
| 2:30:15 PM | Pageview | Homepage | [View Session](https://us.posthog.com/project/12345/replay/session-id) |
| 2:31:02 PM | Pageview | Pricing | [View Session](https://us.posthog.com/project/12345/replay/session-id) |
| 2:35:20 PM | Form Viewed | Contact | [View Session](https://us.posthog.com/project/12345/replay/session-id) |
| 2:40:10 PM | **Form Submitted** | Contact | [View Session](https://us.posthog.com/project/12345/replay/session-id) |

---

### Summary
- New lead from Google Ads campaign
- Visited pricing page before converting
- Successfully submitted contact form
```

---

## Configuration

### PostHog Regions

| Region | Base URL |
|--------|----------|
| US | `https://us.posthog.com` |
| EU | `https://eu.posthog.com` |

If you use EU hosting, update the URLs in `user-journey.md` to use `eu.posthog.com`.

### Customization

You can customize the command by editing `~/.claude/commands/user-journey.md`:

- **Add custom events**: Add your custom event names to the query in Step 4
- **Add page mappings**: Add URL-to-name mappings in the "Page Names" section
- **Add domain labels**: Add your domains in the "Domain Labels" section

---

## Troubleshooting

### Command not found

Make sure the file is in the correct location:
```bash
ls ~/.claude/commands/user-journey.md
```

### PostHog queries failing

1. Verify your PostHog MCP server is connected
2. Check that your API key has the correct permissions
3. Ensure your Project ID is correct

### No results found

- The user might not exist in PostHog
- Try searching by IP address instead of email
- Check if the email property name matches (`person.properties.email`)

---

## Contributing

Feel free to submit PRs with:
- New commands
- Bug fixes
- Documentation improvements

---

## License

MIT
