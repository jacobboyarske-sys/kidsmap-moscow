from datetime import date
from pathlib import Path

from src.data import load_events, merge_events, save_events
from src.scrapers import (
    afisha,
    afisha_yandex,
    kassir,
    kudago,
    meloman,
    mozart_for_kids,
    playforsoul,
    zaryadyehall,
)

EVENTS_PATH = Path("data/events.json")
SEED_PATH = Path("data/seed_events.json")

SCRAPERS = [
    playforsoul,
    mozart_for_kids,
    kudago,
    zaryadyehall,
    meloman,
    afisha_yandex,
    afisha,
    kassir,
]


def main() -> None:
    base_path = EVENTS_PATH if EVENTS_PATH.exists() else SEED_PATH
    events = load_events(base_path)
    before = len(events)

    today = date.today()
    days_to_year_end = (date(today.year, 12, 31) - today).days

    for scraper in SCRAPERS:
        if scraper is kudago:
            scraped = scraper.scrape(days_ahead=days_to_year_end)
        else:
            scraped = scraper.scrape()
        events = merge_events(events, scraped)
        print(f"{scraper.SOURCE}: собрано {len(scraped)}, новых добавлено {len(events) - before}")
        before = len(events)

    save_events(events, EVENTS_PATH)
    print(f"Итого в {EVENTS_PATH}: {len(events)}")


if __name__ == "__main__":
    main()
