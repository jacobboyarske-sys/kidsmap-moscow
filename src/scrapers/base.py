import json
import time
from datetime import date
from pathlib import Path

import requests
import truststore
from bs4 import BeautifulSoup

truststore.inject_into_ssl()

from src.classify import age_text_to_bucket  # noqa: F401 — реэкспорт для скраперов

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

GEOCODE_CACHE_PATH = Path("data/geocode_cache.json")
_geocode_cache: dict[str, list[float] | None] | None = None


def fetch_soup(url: str, timeout: int = 20) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def resolve_year(month_num: int, today: date) -> int:
    return today.year if month_num >= today.month else today.year + 1


def geocode(address: str) -> tuple[float, float] | None:
    """Геокодирует адрес через Nominatim (OpenStreetMap), с файловым кэшем.

    Соблюдает лимит Nominatim в 1 запрос/сек и требование указывать User-Agent.
    """
    global _geocode_cache
    if _geocode_cache is None:
        if GEOCODE_CACHE_PATH.exists():
            with GEOCODE_CACHE_PATH.open(encoding="utf-8") as f:
                _geocode_cache = json.load(f)
        else:
            _geocode_cache = {}

    if address in _geocode_cache:
        cached = _geocode_cache[address]
        return tuple(cached) if cached else None

    coords = None
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "kidsmap-moscow/1.0 (educational project)"},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()
        if results:
            coords = (float(results[0]["lat"]), float(results[0]["lon"]))
    except Exception as e:
        print(f"geocode: не удалось определить координаты «{address}»: {e}")
    finally:
        time.sleep(1)

    _geocode_cache[address] = list(coords) if coords else None
    with GEOCODE_CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(_geocode_cache, f, ensure_ascii=False, indent=2)

    return coords
