import json
from datetime import date

from src.models import AgeLimit, Category, Event
from src.scrapers.base import age_text_to_bucket, fetch_soup, resolve_year

SOURCE = "playforsoul.ru"
AFISHA_URL = "https://playforsoul.ru/afisha"

VENUE_COORDS = {
    "Большой зал в Воронцовском парке": (55.6631, 37.5407),
    "м. Алтуфьево, Алтуфьевское шоссе, 91, Лианозовская библиотека №57": (55.8834, 37.5853),
    "м. Арбатская, Борисоглебский переулок, 6, стр. 1, дом-музей М. Цветаевой": (55.7502, 37.5934),
    "м. Арбатская, Никитский бульвар, д. 7А, театральная гостиная дома Гоголя": (55.7524, 37.6015),
    "м. Курская, Старая Басманная 15Ас4, Галерея «Другое дело»": (55.7649, 37.6602),
    "м. Нагатинская, Варшавское шоссе 33 стр. 13, лофт Only you": (55.6663, 37.6603),
    "м. Нагатинская, лофт Only you": (55.6663, 37.6603),
    "м. Нагатинский Затон, Коломенская ул., 9, стр. 5, Библиотека имени К. М. Симонова": (55.6773, 37.6875),
    "м. Новаторская, Воронцовский парк, 8": (55.6631, 37.5407),
    "м. Свиблово, ул. Седова, д. 3, Библиотека №53": (55.8636, 37.6656),
    "м. Улица 1905 года, ул. 1905 года, д. 3, Библиотека И. Бунина": (55.7656, 37.5476),
    "м. Университет, ул. Строителей, 8, корп. 2, Библиотека имени Данте Алигьери": (55.6906, 37.5326),
    "м. Чкаловская, ул. Земляной Вал, д. 27, стр. 3, Усадьба Толстых-Борисовских": (55.7601, 37.6591),
}

DEFAULT_COORDS = (55.75, 37.62)

THEME_TO_CATEGORY = {
    "Балет": Category.THEATRE,
}
DEFAULT_CATEGORY = Category.CONCERT


def _extract_static_data(soup) -> list[dict]:
    script_text = None
    for tag in soup.find_all("script"):
        if tag.string and "PFS_STATIC_DATA" in tag.string:
            script_text = tag.string
            break

    if script_text is None:
        return []

    start = script_text.index("PFS_STATIC_DATA")
    eq = script_text.index("=", start) + 1
    end = script_text.rindex(";")
    return json.loads(script_text[eq:end].strip())


def _to_event(record: dict, today: date) -> Event | None:
    address = record["Адрес"].replace("\n", " ").strip()
    lat, lon = VENUE_COORDS.get(address, DEFAULT_COORDS)
    if address not in VENUE_COORDS:
        print(f"playforsoul.ru: нет координат для адреса «{address}», использую центр Москвы")

    age_text = record["Возраст"].strip()
    title = record["Название"].strip()
    if title.endswith(age_text):
        title = title[: -len(age_text)].strip()

    theme = record.get("Тематика", "")
    category = THEME_TO_CATEGORY.get(theme, DEFAULT_CATEGORY)

    month_num = record["_month_num"]
    year = resolve_year(month_num, today)
    day = int(record["Число"])
    start_date = date(year, month_num, day)

    price = record.get("Цена", "").strip()

    return Event(
        title=title,
        description=f"Концерт классической музыки для детей: {theme.lower()}." if theme else "Концерт классической музыки для детей.",
        start_date=start_date,
        address=address,
        lat=lat,
        lon=lon,
        category=category,
        age_limit=age_text_to_bucket(age_text),
        price=f"{price} ₽" if price else None,
        url=record.get("Ссылка на полную страницу") or AFISHA_URL,
        source=SOURCE,
    )


def scrape(today: date | None = None) -> list[Event]:
    today = today or date.today()
    soup = fetch_soup(AFISHA_URL)
    records = _extract_static_data(soup)

    events = []
    for record in records:
        try:
            events.append(_to_event(record, today))
        except Exception as e:
            print(f"playforsoul.ru: пропущена запись: {e}")

    return events
