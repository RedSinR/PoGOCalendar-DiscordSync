
import os
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp
import discord

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = int(os.environ["DISCORD_GUILD_ID"])

EVENTS_URL = (
    "https://raw.githubusercontent.com/"
    "bigfoott/ScrapedDuck/data/events.json"
)

TIMEZONE = ZoneInfo("America/Los_Angeles")
DAYS_AHEAD = 60
MAX_EVENTS = 80
PREFIX = "[PoGO]"
LOCATION = "Pokémon GO — in-game event"

def parse_date(value):
    if not value:
        return None

    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"

    result = datetime.fromisoformat(value)

    if result.tzinfo is None:
        result = result.replace(tzinfo=TIMEZONE)

    return result.astimezone(TIMEZONE)


def event_marker(event_id):
    return f"ScrapedDuck event ID: {event_id}"


async def fetch_source_events():
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(EVENTS_URL) as response:
            response.raise_for_status()
            data = await response.json()

    if not isinstance(data, list):
        raise ValueError("Unexpected event feed format")

    return data


async def sync_events():
    now = datetime.now(TIMEZONE)
    cutoff = now + timedelta(days=DAYS_AHEAD)

    source_events = await fetch_source_events()
    candidates = []

    for item in source_events:
        event_id = item.get("eventID")
        name = item.get("name")
        start = parse_date(item.get("start"))
        end = parse_date(item.get("end"))

        if not event_id or not name or not start or not end:
            continue

        if end <= now or start >= cutoff or end <= start:
            continue

        candidates.append({
            "id": str(event_id),
            "name": str(name)[:90],
            "start": start,
            "end": end,
            "link": item.get("link", ""),
            "type": item.get("heading", item.get("eventType", "")),
        })

    candidates.sort(key=lambda event: event["start"])
    candidates = candidates[:MAX_EVENTS]

    intents = discord.Intents.none()
    intents.guilds = True
    client = discord.Client(intents=intents)

    try:
        await client.login(TOKEN)

        guild = client.get_guild(GUILD_ID)
        if guild is None:
            guild = await client.fetch_guild(GUILD_ID)

        existing = await guild.fetch_scheduled_events()
        managed = [
            event for event in existing
            if event.name.startswith(PREFIX)
        ]

        by_marker = {}
        for event in managed:
            description = event.description or ""
            for line in description.splitlines():
                if line.startswith("ScrapedDuck event ID: "):
                    event_id = line.split(": ", 1)[1].strip()
                    by_marker[event_id] = event

        wanted_ids = {event["id"] for event in candidates}

        for item in candidates:
            marker = event_marker(item["id"])
            description = (
                f"{item['type']}\n"
                f"{item['link']}\n\n"
                f"{marker}"
            )[:1000]

            event_name = f"{PREFIX} {item['name']}"[:100]

            current = by_marker.get(item["id"])

            if current:
                changed = (
                    current.name != event_name
                    or current.description != description
                    or current.start_time != item["start"]
                    or current.end_time != item["end"]
                )

                if changed:
                    await current.edit(
                        name=event_name,
                        description=description,
                        start_time=item["start"],
                        end_time=item["end"],
                        location=LOCATION,
                        reason="PoGO calendar sync",
                    )
                    print(f"Updated: {event_name}")
            else:
                await guild.create_scheduled_event(
                    name=event_name,
                    description=description,
                    start_time=item["start"],
                    end_time=item["end"],
                    location=LOCATION,
                    privacy_level=discord.PrivacyLevel.guild_only,
                    entity_type=discord.EntityType.external,
                    reason="PoGO calendar sync",
                )
                print(f"Created: {event_name}")

        for event in managed:
            description = event.description or ""
            marker_id = None

            for line in description.splitlines():
                if line.startswith("ScrapedDuck event ID: "):
                    marker_id = line.split(": ", 1)[1].strip()
                    break

            if marker_id and marker_id not in wanted_ids:
                await event.delete(reason="PoGO event no longer in sync window")
                print(f"Removed expired/out-of-window event: {event.name}")

        print(f"Sync finished. Source events considered: {len(candidates)}")

    finally:
        await client.close()


async def main():
    await sync_events()


if __name__ == "__main__":
    asyncio.run(main())
