import json
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from src.models import AgeLimit, Category, Event


def load_events(path: Path = Path("data/events.json")) -> list[Event]:
    if not path.exists():
        return []

    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    events = []
    for i, record in enumerate(records):
        try:
            events.append(Event(**record))
        except ValidationError as e:
            print(f"Пропущена запись #{i}: {e}")

    return events


def event_key(event: Event) -> tuple[str, str, str]:
    return (event.source, event.title, str(event.start_date))


def merge_events(existing: list[Event], scraped: list[Event]) -> list[Event]:
    existing_keys = {event_key(e) for e in existing}
    new_events = [e for e in scraped if event_key(e) not in existing_keys]
    return existing + new_events


def save_events(events: list[Event], path: Path = Path("data/events.json")) -> None:
    records = [e.model_dump(mode="json") for e in events]
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def filter_events(
    events: list[Event],
    date_from: date,
    date_to: date,
    categories: list[Category],
    age_limits: list[AgeLimit],
) -> list[Event]:
    return [
        e
        for e in events
        if date_from <= e.start_date <= date_to
        and e.category in categories
        and e.age_limit in age_limits
    ]
