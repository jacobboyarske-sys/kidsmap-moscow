import re
from datetime import date

from src.models import Category, Event
from src.scrapers.base import age_text_to_bucket, fetch_soup, resolve_year

SOURCE = "mozart-for-kids.ru"
HOME_URL = "https://mozart-for-kids.ru"

MONTHS = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}

VENUE_COORDS = {
    "Домик в поселке художников": (55.8047, 37.5147),
    "Проспект Вернадского, д. 69": (55.6767, 37.5136),
    "ул. 1812 года, д.2": (55.7317, 37.5119),
    "ул. Покровский бульвар, 16-18, стр.4-4а": (55.7558, 37.6339),
    "ул. Профсоюзная, д. 68к1": (55.6785, 37.5537),
    "ул. Сельскохозяйственная, д. 37": (55.8267, 37.6403),
}
DEFAULT_COORDS = (55.75, 37.62)

TITLE_RE = re.compile(r"«([^»]+)»\s+(\d{1,2})\s+(\S+)")
AGE_RE = re.compile(r"(\d+)\+")
ADDRESS_PREFIX_RE = re.compile(r"^Адрес\s*:?\s*")


def _to_event(raw_title: str, raw_descr: str, today: date) -> Event | None:
    match = TITLE_RE.search(raw_title)
    if not match:
        return None

    title, day_text, month_name = match.groups()
    month_num = MONTHS.get(month_name)
    if month_num is None:
        return None

    year = resolve_year(month_num, today)
    start_date = date(year, month_num, int(day_text))

    age_match = AGE_RE.search(raw_title)
    age_text = age_match.group(0) if age_match else "0+"

    address = ADDRESS_PREFIX_RE.sub("", raw_descr).strip()
    lat, lon = VENUE_COORDS.get(address, DEFAULT_COORDS)
    if address not in VENUE_COORDS:
        print(f"{SOURCE}: нет координат для адреса «{address}», использую центр Москвы")

    category = Category.WORKSHOP if "ступеньк" in title.lower() or "занят" in title.lower() else Category.CONCERT
    description = (
        "Регулярные музыкальные занятия для малышей."
        if category == Category.WORKSHOP
        else "Концерт классической музыки для детей."
    )

    return Event(
        title=title,
        description=description,
        start_date=start_date,
        address=address,
        lat=lat,
        lon=lon,
        category=category,
        age_limit=age_text_to_bucket(age_text),
        url=HOME_URL,
        source=SOURCE,
    )


def scrape(today: date | None = None) -> list[Event]:
    today = today or date.today()
    soup = fetch_soup(HOME_URL)
    cards = soup.select("div.t778__col.js-product")

    events = []
    for card in cards:
        title_tag = card.select_one(".js-product-name")
        descr_tag = card.select_one(".t778__descr")
        if not title_tag or not descr_tag:
            continue

        try:
            event = _to_event(
                title_tag.get_text(strip=True), descr_tag.get_text(strip=True), today
            )
            if event:
                events.append(event)
        except Exception as e:
            print(f"{SOURCE}: пропущена запись: {e}")

    return events
