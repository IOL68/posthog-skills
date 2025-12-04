#!/usr/bin/env python3
"""
Create PostHog Session Replay playlists with common filters.

Usage:
    python create_playlist.py --api-key API_KEY --project-id PROJECT_ID --name "Name" --filter-type TYPE [options]

Filter types:
    person_property  - Filter by person property (requires --property-key, --property-value or --is-set)
    event           - Filter by event (requires --event-name)
    url             - Filter by URL (requires --url)
    rage_clicks     - Sessions with rage clicks
    console_errors  - Sessions with console errors
    mobile          - Mobile device sessions

Examples:
    # LinkedIn Ad visitors
    python create_playlist.py --api-key phx_xxx --project-id 12345 --name "LinkedIn Visitors" \
        --filter-type person_property --property-key li_fat_id --is-set --host thelai.com

    # Rage clicks
    python create_playlist.py --api-key phx_xxx --project-id 12345 --name "Rage Clicks" \
        --filter-type rage_clicks --host thelai.com

    # Specific URL
    python create_playlist.py --api-key phx_xxx --project-id 12345 --name "Checkout Sessions" \
        --filter-type url --url "/checkout"
"""

import argparse
import json
import sys
import urllib.request
import urllib.error


def build_filter_group(args):
    """Build the filter_group based on filter type."""
    filters = []

    # Add host filter if provided
    if args.host:
        hosts = [args.host]
        if not args.host.startswith('www.'):
            hosts.append(f'www.{args.host}')
        filters.append({
            "id": "$pageview",
            "name": "$pageview",
            "type": "events",
            "properties": [
                {"key": "$host", "type": "event", "value": hosts, "operator": "exact"}
            ]
        })

    # Add specific filter based on type
    if args.filter_type == 'person_property':
        if args.is_set:
            filters.append({
                "key": args.property_key,
                "type": "person",
                "operator": "is_set",
                "value": "is_set"
            })
        else:
            filters.append({
                "key": args.property_key,
                "type": "person",
                "operator": "exact",
                "value": [args.property_value] if args.property_value else []
            })

    elif args.filter_type == 'event':
        event_filter = {
            "id": args.event_name,
            "name": args.event_name,
            "type": "events",
            "order": 0
        }
        if args.event_property_key:
            event_filter["properties"] = [{
                "key": args.event_property_key,
                "type": "event",
                "value": args.event_property_value,
                "operator": "exact"
            }]
        filters.append(event_filter)

    elif args.filter_type == 'url':
        filters.append({
            "id": "$pageview",
            "name": "$pageview",
            "type": "events",
            "properties": [
                {"key": "$current_url", "type": "event", "value": args.url, "operator": "icontains"}
            ]
        })

    elif args.filter_type == 'rage_clicks':
        filters.append({"id": "$rageclick", "type": "events", "order": 0})

    elif args.filter_type == 'console_errors':
        filters.append({
            "key": "level",
            "type": "log_entry",
            "value": ["error"],
            "operator": "exact"
        })

    elif args.filter_type == 'mobile':
        filters.append({
            "key": "snapshot_source",
            "type": "recording",
            "value": ["mobile"],
            "operator": "exact"
        })

    return {
        "type": "AND",
        "values": [{"type": "AND", "values": filters}]
    }


def create_playlist(args):
    """Create the playlist via PostHog API."""
    host = args.posthog_host or "us.posthog.com"
    url = f"https://{host}/api/projects/{args.project_id}/session_recording_playlists/"

    payload = {
        "name": args.name,
        "description": args.description or "",
        "type": "filters",
        "filters": {
            "order": "start_time",
            "date_from": args.date_from or "-30d",
            "duration": [{"key": "active_seconds", "type": "recording", "value": 5, "operator": "gt"}],
            "filter_group": build_filter_group(args),
            "order_direction": "DESC",
            "filter_test_accounts": args.filter_test_accounts
        }
    }

    data = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {args.api_key}')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))

            print(f"Playlist created successfully!")
            print(f"  Name: {result['name']}")
            print(f"  ID: {result['id']}")
            print(f"  Short ID: {result['short_id']}")
            print(f"  URL: https://{host}/project/{args.project_id}/replay/playlists/{result['short_id']}")

            return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Error: {e.code} - {error_body}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Create PostHog Session Replay playlists')

    # Required arguments
    parser.add_argument('--api-key', required=True, help='PostHog Personal API Key (phx_...)')
    parser.add_argument('--project-id', required=True, help='PostHog Project ID')
    parser.add_argument('--name', required=True, help='Playlist name')
    parser.add_argument('--filter-type', required=True,
                        choices=['person_property', 'event', 'url', 'rage_clicks', 'console_errors', 'mobile'],
                        help='Type of filter to create')

    # Optional arguments
    parser.add_argument('--description', help='Playlist description')
    parser.add_argument('--host', help='Filter by host/domain (e.g., thelai.com)')
    parser.add_argument('--posthog-host', default='us.posthog.com', help='PostHog host (us.posthog.com or eu.posthog.com)')
    parser.add_argument('--date-from', default='-30d', help='Date range (e.g., -30d, -90d)')
    parser.add_argument('--filter-test-accounts', action='store_true', help='Filter out test accounts')

    # Person property filter options
    parser.add_argument('--property-key', help='Person property key (for person_property filter)')
    parser.add_argument('--property-value', help='Person property value (for person_property filter)')
    parser.add_argument('--is-set', action='store_true', help='Check if property is set (for person_property filter)')

    # Event filter options
    parser.add_argument('--event-name', help='Event name (for event filter)')
    parser.add_argument('--event-property-key', help='Event property key')
    parser.add_argument('--event-property-value', help='Event property value')

    # URL filter options
    parser.add_argument('--url', help='URL to filter (for url filter)')

    args = parser.parse_args()

    # Validate required options for each filter type
    if args.filter_type == 'person_property' and not args.property_key:
        parser.error("--property-key is required for person_property filter")
    if args.filter_type == 'event' and not args.event_name:
        parser.error("--event-name is required for event filter")
    if args.filter_type == 'url' and not args.url:
        parser.error("--url is required for url filter")

    create_playlist(args)


if __name__ == '__main__':
    main()
