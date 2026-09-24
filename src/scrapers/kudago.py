import time
from datetime import date, datetime, timedelta

import requests

from src.models import Category, Event

SOURCE = "kudago.com"
API_URL = "https://kudago.com/public-api/v1.4/events/"

CATEGORY_MAP = {
    "theater": Category.THEATRE,
    "concert": Category.CONCERT,
    "quest": Category.QUEST,
    "tour": Category.EXCURSION,
    "excursion": Category.EXCURSION,
    "party": Category.HOLIDAY,
    "sport": Category.SPORT,
    "cinema": Category.CINEMA,
    "movie": Category.CINEMA,
    "education": Category.WORKSHOP,
    "exhibition": Category.EXCURSION,
}
DEFAULT_CATEGORY = Category.WORKSHOP


def _resolve_category(tags: list[str]) -> Category:
    for tag in tags:
        if tag in CATEGORY_MAP:
            return CATEGORY_MAP[tag]
    return DEFAULT_CATEGORY


def _pick_date_range(dates: list[dict], now: int) -> tuple[int, int | None] | None:
    for d in dates:
        if d["end"] >= now:
            return d["start"], d["end"]
    return None


def _to_event(record: dict, now: int, today: date) -> Event | None:
    date_range = _pick_date_range(record["dates"], now)
    if date_range is None:
        return None
    start_ts, end_ts = date_range

    try:
        start_date = datetime.fromtimestamp(start_ts).date() if start_ts > 0 else today
    except (OSError, OverflowError, ValueError):
        start_date = today

    end_date = None
    if end_ts and end_ts > 0:
        try:
            candidate = datetime.fromtimestamp(end_ts).date()
            if candidate >= start_date:
                end_date = candidate
        except (OSError, OverflowError, ValueError):
            pass

    place = record.get("place") or {}
    coords = place.get("coords") or {}
    lat, lon = coords.get("lat"), coords.get("lon")
    if lat is None or lon is None:
        return None

    address = place.get("address") or place.get("title") or "Москва"

    age_text = str(record.get("age_restriction") or "0")
    from src.scrapers.base import age_text_to_bucket

    price = (record.get("price") or "").replace("рублей", "₽").strip()

    description = (record.get("description") or "").strip()
    if len(description) > 300:
        description = description[:297] + "..."

    return Event(
        title=record["title"].strip().capitalize(),
        description=description or "Событие для детей в Москве.",
        start_date=start_date,
        end_date=end_date,
        address=address,
        lat=lat,
        lon=lon,
        category=_resolve_category(record.get("categories", [])),
        age_limit=age_text_to_bucket(age_text),
        price=price or None,
        url=record.get("site_url") or "https://kudago.com/msk/",
        source=SOURCE,
    )


def scrape(today: date | None = None, days_ahead: int = 45) -> list[Event]:
    today = today or date.today()
    now = int(time.time())
    until = now + days_ahead * 24 * 3600

    events = []
    url = API_URL
    params = {
        "location": "msk",
        "categories": "kids",
        "fields": "id,title,description,dates,place,price,age_restriction,categories,site_url",
        "expand": "place",
        "actual_since": now,
        "actual_until": until,
        "text_format": "plain",
        "page_size": 100,
    }

    while url:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        for record in data["results"]:
            try:
                event = _to_event(record, now, today)
                if event:
                    events.append(event)
            except Exception as e:
                print(f"{SOURCE}: пропущена запись: {e}")

        url = data.get("next")
        params = None  # next уже содержит все параметры в самой ссылке

    return events
