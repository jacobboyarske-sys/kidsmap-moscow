import json
from pathlib import Path

from pydantic import ValidationError

from src.models import Event


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
