import json
import re
from datetime import date, datetime

from src.models import Category, Event
from src.scrapers.base import HEADERS, age_text_to_bucket, fetch_soup, geocode

import requests

SOURCE = "afisha.ru"
HOME_URL = "https://www.afisha.ru"
LIST_URL = f"{HOME_URL}/msk/schedule_kids/concerts/"

DEFAULT_COORDS = (55.75, 37.62)

AGE_RE = re.compile(r"Возраст\s+(\d{1,2}\+)")


def _load_nrp_model(soup) -> dict:
    for script in soup.find_all("script"):
        text = script.string or ""
        if text.startswith("(window.__nrp"):
            idx = text.index("['root'] = ")
            rest = text[idx + len("['root'] = "):]
            json_str = rest.split(";window.__nrpBoot")[0].strip()
            return json.loads(json_str)
    return {}


def _fetch_age(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    from bs4 import BeautifulSoup

    detail_soup = BeautifulSoup(response.text, "html.parser")
    text = detail_soup.get_text(" ", strip=True)
    match = AGE_RE.search(text)
    return match.group(1) if match else "0+"


def _to_event(item: dict) -> Event | None:
    place = item.get("Notice", {}).get("Place")
    if not place:
        return None

    min_date = item.get("ScheduleInfo", {}).get("MinScheduleDate")
    if not min_date:
        return None
    start_date = datetime.fromisoformat(min_date).date()

    title = item["Name"]
    venue_name = place["Name"]
    venue_address = place.get("Address") or ""
    address = f"{venue_name}, {venue_address}".strip(", ")

    coords = geocode(f"{venue_name}, Москва") or geocode(f"Москва, {venue_address}")
    if coords is None:
        print(f"{SOURCE}: нет координат для площадки «{venue_name}», использую центр Москвы")
    lat, lon = coords if coords else DEFAULT_COORDS

    url = f"{HOME_URL}{item['Url']}"
    description = item.get("Description") or title

    try:
        age_text = _fetch_age(url)
    except Exception:
        age_text = "0+"

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
    model = _load_nrp_model(soup)
    items = model.get("model", {}).get("ScheduleWidget", {}).get("Items", [])

    events = []
    for item in items:
        try:
            event = _to_event(item)
            if event:
                events.append(event)
        except Exception as e:
            print(f"{SOURCE}: пропущена запись «{item.get('Name')}»: {e}")

    return events
