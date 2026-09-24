from datetime import date

import requests
from bs4 import BeautifulSoup

from src.classify import age_text_to_bucket  # noqa: F401 — реэкспорт для скраперов

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def fetch_soup(url: str, timeout: int = 20) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def resolve_year(month_num: int, today: date) -> int:
    return today.year if month_num >= today.month else today.year + 1
