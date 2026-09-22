import json
from pathlib import Path

from pydantic import ValidationError

from src.models import Event

SEED_PATH = Path("data/seed_events.json")


def main() -> None:
    with SEED_PATH.open(encoding="utf-8") as f:
        records = json.load(f)

    valid_count = 0
    for i, record in enumerate(records):
        try:
            Event(**record)
            valid_count += 1
        except ValidationError as e:
            print(f"#{i}: {e}")

    print(f"Валидно: {valid_count}/{len(records)}")


if __name__ == "__main__":
    main()
