import re
from datetime import date, datetime

from src.models import Category, Event
from src.scrapers.base import age_text_to_bucket, fetch_soup

SOURCE = "meloman.ru"
HOME_URL = "https://meloman.ru"
LIST_URL = f"{HOME_URL}/kids/concerts/"

VENUE_INFO = {
    "Ф2. Концертный зал имени С. В. Рахманинова": (
        "Олимпийский проспект, 14, Филармония-2",
        55.7854,
        37.6318,
    ),
    "Ф2. Игровой зал": ("Олимпийский проспект, 14, Филармония-2", 55.7854, 37.6318),
    "Ф2. Виртуальный зал": ("Олимпийский проспект, 14, Филармония-2", 55.7854, 37.6318),
    "Концертный зал имени П. И. Чайковского": (
        "Триумфальная площадь, 4/31",
        55.7697,
        37.5966,
    ),
    "Камерный зал Филармонии": ("Кадашёвская набережная, 26", 55.7423, 37.6236),
}
DEFAULT_ADDRESS_COORDS = ("Москва", 55.75, 37.62)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def _to_event(card) -> Event | None:
    time_tag = card.select_one("time.info-accent[datetime]")
    title_tag = card.select_one(".article-ticket__editor b.uppercase")
    if not time_tag or not title_tag:
        return None

    start_date = datetime.strptime(time_tag["datetime"], "%d.%m.%Y %H:%M").date()
    title = _normalize(title_tag.get_text())

    age_tag = card.select_one(".article-ticket__header span.info-accent")
    age_text = age_tag.get_text(strip=True) if age_tag else "0+"

    venue_tag = card.select_one(".article-ticket__toolbar .editor--toolbar")
    venue_name = _normalize(venue_tag.get_text(" ")) if venue_tag else ""
    address, lat, lon = VENUE_INFO.get(venue_name, DEFAULT_ADDRESS_COORDS)
    if venue_name not in VENUE_INFO:
        print(f"{SOURCE}: нет координат для зала «{venue_name}», использую центр Москвы")

    desc_paragraphs = card.select(".article-ticket__editor .editor--preview p")
    description = ""
    if len(desc_paragraphs) > 1:
        description = _normalize(desc_paragraphs[1].get_text())
    if not description:
        description = title

    link_tag = card.select_one(".article-ticket__picture a")
    href = link_tag.get("href", "") if link_tag else ""
    url = f"{HOME_URL}{href}" if href else LIST_URL

    return Event(
        title=title,
        description=description,
        start_date=start_date,
        address=address,
        lat=lat,
        lon=lon,
        category=Category.CONCERT,
        age_limit=age_text_to_bucket(age_text),
        url=url,
        source=SOURCE,
    )


def scrape(today: date | None = None) -> list[Event]:
    soup = fetch_soup(LIST_URL)
    cards = soup.select(".article-ticket")

    events = []
    for card in cards:
        try:
            event = _to_event(card)
            if event:
                events.append(event)
        except Exception as e:
            print(f"{SOURCE}: пропущена запись: {e}")

    return events
