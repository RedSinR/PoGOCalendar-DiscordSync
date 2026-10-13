
import os
import asyncio
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import aiohttp

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = os.environ["DISCORD_GUILD_ID"]

EVENTS_URL = (
    "https://raw.githubusercontent.com/"
    "bigfoott/ScrapedDuck/data/events.json"
)

DISCORD_API = "https://discord.com/api/v10"
TIMEZONE = ZoneInfo("America/Los_Angeles")
DAYS_AHEAD = 60
MAX_EVENTS = 80
PREFIX = "[PoGO]"
LOCATION = "Pokémon GO — in-game event"
MARKER_PREFIX = "ScrapedDuck event ID: "


def parse_date(value):
    if not value:
        return None

    try:
        value = value.strip()

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        result = datetime.fromisoformat(value)

        if result.tzinfo is None:
            result = result.replace(tzinfo=TIMEZONE)

        return result.astimezone(timezone.utc)

    except (ValueError, TypeError, AttributeError):
        return None


def event_marker(event_id):
    return f"{MARKER_PREFIX}{event_id}"


def discord_time(value):
    return value.astimezone(timezone.utc).isoformat()


async def fetch_source_events(session):
    async with session.get(EVENTS_URL) as response:
        response.raise_for_status()
        data = await response.json(content_type=None)

    if not isinstance(data, list):
        raise ValueError("Unexpected event feed format.")

    return data


async def discord_request(session, method, path, **kwargs):
    url = f"{DISCORD_API}{path}"

    # Retry rate limits and temporary Discord server errors.
    for attempt in range(10):
        async with session.request(
            method, url, **kwargs
        ) as response:
            body = await response.text()
            status = response.status

            if 200 <= status < 300:
                return json.loads(body) if body else None

            if status == 429:
                try:
                    error_data = json.loads(body)
                    wait_seconds = float(
                        error_data.get("retry_after", 5)
                    )
                except (ValueError, TypeError):
                    wait_seconds = 5

                wait_seconds = max(wait_seconds, 1) + 1

                print(
                    f"Discord rate limit reached. "
                    f"Waiting {wait_seconds:.1f} seconds "
                    f"(attempt {attempt + 1}/10)..."
                )
                await asyncio.sleep(wait_seconds)
                continue

            if status >= 500 and attempt < 9:
                wait_seconds = min(2 ** attempt, 30)
                print(
                    f"Discord server error {status}. "
                    f"Retrying in {wait_seconds} seconds..."
                )
                await asyncio.sleep(wait_seconds)
                continue

            raise RuntimeError(
                f"Discord API error {status}: {body}"
            )

    raise RuntimeError(
        f"Discord request failed after repeated retries: "
        f"{method} {path}"
    )


def get_marker(event):
    description = event.get("description") or ""

    for line in description.splitlines():
        if line.startswith(MARKER_PREFIX):
            return line[len(MARKER_PREFIX):].strip()

    return None


async def sync_events():
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=DAYS_AHEAD)

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "PoGOCalendarSync/1.0",
    }

    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(
        timeout=timeout,
        headers=headers,
    ) as session:

        print("Downloading Pokémon GO event calendar...")
        source_events = await fetch_source_events(session)

        candidates = []

        for item in source_events:
            event_id = item.get("eventID")
            name = item.get("name")
            start = parse_date(item.get("start"))
            end = parse_date(item.get("end"))

            if not event_id or not name or not start or not end:
                continue

            # Discord cannot create scheduled events in the past.
            if start <= now or start >= cutoff or end <= start:
                continue

            candidates.append({
                "id": str(event_id),
                "name": str(name)[:90],
                "start": start,
                "end": end,
                "link": str(item.get("link") or ""),
                "type": str(
                    item.get("heading")
                    or item.get("eventType")
                    or ""
                ),
            })

        candidates.sort(key=lambda event: event["start"])
        candidates = candidates[:MAX_EVENTS]

        print(f"Upcoming source events selected: {len(candidates)}")

        path = f"/guilds/{GUILD_ID}/scheduled-events"

        existing = await discord_request(
            session,
            "GET",
            path,
            params={"with_user_count": "false"},
        )

        # Manage only events carrying our unique source marker.
        managed = {}

        for event in existing:
            marker_id = get_marker(event)
            if marker_id is not None:
                managed[marker_id] = event

        wanted_ids = {event["id"] for event in candidates}

        for item in candidates:
            marker = event_marker(item["id"])

            description = "\n".join([
                item["type"],
                item["link"],
                "",
                marker,
                "Event data: ScrapedDuck / LeekDuck",
            ])[:1000]

            event_name = f"{PREFIX} {item['name']}"[:100]

            payload = {
                "name": event_name,
                "description": description,
                "scheduled_start_time": discord_time(item["start"]),
                "scheduled_end_time": discord_time(item["end"]),
                "privacy_level": 2,
                "entity_type": 3,
                "entity_metadata": {"location": LOCATION},
            }

            current = managed.get(item["id"])

            if current:
                unchanged = (
                    current.get("name") == event_name
                    and (current.get("description") or "") == description
                    and parse_date(current.get("scheduled_start_time"))
                    == item["start"]
                    and parse_date(current.get("scheduled_end_time"))
                    == item["end"]
                    and (
                        (current.get("entity_metadata") or {}).get("location")
                        == LOCATION
                    )
                )

                if unchanged:
                    print(f"Unchanged: {event_name}")
                    continue

                await discord_request(
                    session,
                    "PATCH",
                    f"{path}/{current['id']}",
                    json=payload,
                )
                print(f"Updated: {event_name}")

            else:
                await discord_request(
                    session,
                    "POST",
                    path,
                    json=payload,
                )
                print(f"Created: {event_name}")

        # Remove only our marked events no longer in the selected window.
        for marker_id, event in managed.items():
            if marker_id not in wanted_ids:
                await discord_request(
                    session,
                    "DELETE",
                    f"{path}/{event['id']}",
                )
                print(
                    f"Removed old bot-managed event: "
                    f"{event.get('name')}"
                )

        print("Sync completed successfully.")


async def main():
    await sync_events()


if __name__ == "__main__":
    asyncio.run(main())
