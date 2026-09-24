from pathlib import Path

from src.data import load_events, merge_events, save_events
from src.scrapers import kudago, mozart_for_kids, playforsoul

EVENTS_PATH = Path("data/events.json")
SEED_PATH = Path("data/seed_events.json")

SCRAPERS = [playforsoul, mozart_for_kids, kudago]


def main() -> None:
    base_path = EVENTS_PATH if EVENTS_PATH.exists() else SEED_PATH
    events = load_events(base_path)
    before = len(events)

    for scraper in SCRAPERS:
        scraped = scraper.scrape()
        events = merge_events(events, scraped)
        print(f"{scraper.SOURCE}: собрано {len(scraped)}, новых добавлено {len(events) - before}")
        before = len(events)

    save_events(events, EVENTS_PATH)
    print(f"Итого в {EVENTS_PATH}: {len(events)}")


if __name__ == "__main__":
    main()
