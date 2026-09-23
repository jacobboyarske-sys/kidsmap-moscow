import json
from datetime import date
from pathlib import Path

from pydantic import ValidationError

from src.models import AgeLimit, Category, Event


def load_events(path: Path = Path("data/seed_events.json")) -> list[Event]:
    with path.open(encoding="utf-8") as f:
        records = json.load(f)

    events = []
    for i, record in enumerate(records):
        try:
            events.append(Event(**record))
        except ValidationError as e:
            print(f"Пропущена запись #{i}: {e}")

    return events


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
