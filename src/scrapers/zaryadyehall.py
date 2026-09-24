import re
from datetime import date

from src.models import Category, Event
from src.scrapers.base import age_text_to_bucket, fetch_soup, resolve_year

SOURCE = "zaryadyehall.ru"
HOME_URL = "https://zaryadyehall.ru"
LIST_URL = f"{HOME_URL}/events/for-kids/"

ADDRESS = "Москва, ул. Варварка, 6с4"
COORDS = (55.7513, 37.6284)

DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})")


def _parse_date(date_text: str, today: date) -> date | None:
    match = DATE_RE.search(date_text)
    if not match:
        return None
    day, month = int(match.group(1)), int(match.group(2))
    year = resolve_year(month, today)
    return date(year, month, day)


def _to_event(item, start_date: date) -> Event | None:
    title_tag = item.select_one(".events__item_title a")
    if not title_tag:
        return None
    title = re.sub(r"\s+", " ", " ".join(title_tag.stripped_strings)).strip()

    link = title_tag.get("href", "")
    url = f"{HOME_URL}{link}" if link else LIST_URL

    age_tag = item.select_one(".events__item_tags .tag")
    age_text = age_tag.get_text(strip=True) if age_tag else "0+"

    desc_tag = item.select_one(".events__item_desc")
    description = desc_tag.get_text(strip=True) if desc_tag else title

    return Event(
        title=title,
        description=description,
        start_date=start_date,
        address=ADDRESS,
        lat=COORDS[0],
        lon=COORDS[1],
        category=Category.CONCERT,
        age_limit=age_text_to_bucket(age_text),
        url=url,
        source=SOURCE,
    )


def scrape(today: date | None = None) -> list[Event]:
    today = today or date.today()
    soup = fetch_soup(LIST_URL)
    rows = soup.select(".events__content_row")

    events = []
    for row in rows:
        date_tag = row.select_one(".events__date")
        if not date_tag:
            continue
        start_date = _parse_date(date_tag.get_text(strip=True), today)
        if start_date is None:
            continue

        for item in row.select(".events__item"):
            try:
                event = _to_event(item, start_date)
                if event:
                    events.append(event)
            except Exception as e:
                print(f"{SOURCE}: пропущена запись: {e}")

    return events
