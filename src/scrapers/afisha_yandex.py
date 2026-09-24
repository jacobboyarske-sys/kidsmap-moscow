import json
import re
from datetime import date, datetime

from src.models import Category, Event
from src.scrapers.base import HEADERS, age_text_to_bucket, fetch_soup, geocode

import requests

SOURCE = "afisha.yandex.ru"
HOME_URL = "https://afisha.yandex.ru"
LIST_URL = f"{HOME_URL}/moscow/selections/kids-concert-kids"

DEFAULT_COORDS = (55.75, 37.62)

_UNDEFINED_RE = re.compile(r":undefined")
_NEW_DATE_RE = re.compile(r'new Date\("([^"]+)"\)')
_DETAIL_RE = re.compile(
    r"^(?P<title>.+?), (?P<venue>.+?), купить билеты.*?, (?P<date>\d{2}\.\d{2}\.\d{4})\."
)


def _load_apollo_state(soup) -> dict:
    for script in soup.find_all("script"):
        text = script.string or ""
        if text.startswith("window['__APOLLO_STATE__']"):
            json_str = text.split("=", 1)[1].strip()
            if json_str.endswith(";"):
                json_str = json_str[:-1]
            json_str = _NEW_DATE_RE.sub(r'"\1"', json_str)
            json_str = _UNDEFINED_RE.sub(":null", json_str)
            return json.loads(json_str)
    return {}


def _fetch_detail(url: str, age_text: str, today: date) -> Event | None:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    from bs4 import BeautifulSoup

    detail_soup = BeautifulSoup(response.text, "html.parser")
    meta = detail_soup.find("meta", attrs={"name": "description"})
    if not meta or not meta.get("content"):
        return None

    match = _DETAIL_RE.match(meta["content"])
    if not match:
        return None

    title = match.group("title").strip()
    venue = match.group("venue").strip()
    start_date = datetime.strptime(match.group("date"), "%d.%m.%Y").date()

    coords = geocode(f"Москва, {venue}")
    if coords is None:
        print(f"{SOURCE}: нет координат для площадки «{venue}», использую центр Москвы")
    lat, lon = coords if coords else DEFAULT_COORDS

    return Event(
        title=title,
        description=title,
        start_date=start_date,
        address=venue,
        lat=lat,
        lon=lon,
        category=Category.CONCERT,
        age_limit=age_text_to_bucket(age_text),
        url=url,
        source=SOURCE,
    )


def scrape(today: date | None = None) -> list[Event]:
    today = today or date.today()
    soup = fetch_soup(LIST_URL)
    data = _load_apollo_state(soup)

    previews = [
        v for v in data.values() if isinstance(v, dict) and v.get("__typename") == "EventPreview"
    ]

    events = []
    for preview in previews:
        path = preview.get("url")
        if not path:
            continue
        try:
            event = _fetch_detail(
                f"{HOME_URL}{path}", preview.get("contentRating") or "0+", today
            )
            if event:
                events.append(event)
        except Exception as e:
            print(f"{SOURCE}: пропущена запись {path}: {e}")

    return events
