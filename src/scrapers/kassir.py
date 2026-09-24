import re
from datetime import date, datetime

from src.models import Category, Event
from src.scrapers.base import age_text_to_bucket, fetch_soup, geocode

SOURCE = "msk.kassir.ru"
HOME_URL = "https://msk.kassir.ru"
LIST_URL = f"{HOME_URL}/selection/kontsertyi-dlya-detey"

DEFAULT_COORDS = (55.75, 37.62)

CATEGORY_BY_PREFIX = {
    "teatr": Category.THEATRE,
    "koncert": Category.CONCERT,
    "ekskursii": Category.EXCURSION,
    "obrazovanie": Category.WORKSHOP,
}
DEFAULT_CATEGORY = Category.CONCERT

AGE_RE = re.compile(r"^\d{1,2}\+$")


def _to_event(card) -> Event | None:
    title_tag = card.select_one("h2.compilation-tile__title")
    link_tag = card.select_one("a[href]")
    time_tag = card.select_one("time.compilation-tile__date[datetime]")
    venue_tag = card.select_one("a.compilation-tile__venue")
    if not title_tag or not link_tag or not time_tag:
        return None

    title = title_tag.get_text(strip=True)
    href = link_tag["href"]
    url = f"{HOME_URL}{href}"
    start_date = datetime.fromisoformat(time_tag["datetime"]).date()

    prefix = href.strip("/").split("/")[0]
    category = CATEGORY_BY_PREFIX.get(prefix, DEFAULT_CATEGORY)

    venue = venue_tag.get_text(strip=True) if venue_tag else ""

    age_text = "0+"
    for badge in card.select("div"):
        text = badge.get_text(strip=True)
        if AGE_RE.match(text):
            age_text = text
            break

    coords = geocode(f"{venue}, Москва") if venue else None
    if coords is None:
        print(f"{SOURCE}: нет координат для площадки «{venue}», использую центр Москвы")
    lat, lon = coords if coords else DEFAULT_COORDS

    return Event(
        title=title,
        description=title,
        start_date=start_date,
        address=venue or "Москва",
        lat=lat,
        lon=lon,
        category=category,
        age_limit=age_text_to_bucket(age_text),
        url=url,
        source=SOURCE,
    )


def scrape(today: date | None = None) -> list[Event]:
    soup = fetch_soup(LIST_URL)
    cards = soup.select("article.compilation-tile")

    events = []
    for card in cards:
        try:
            event = _to_event(card)
            if event:
                events.append(event)
        except Exception as e:
            print(f"{SOURCE}: пропущена запись: {e}")

    return events
