from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Category(str, Enum):
    THEATRE = "театр"
    WORKSHOP = "мастер-класс"
    QUEST = "квест"
    SPORT = "спорт"
    CINEMA = "кино"
    EXCURSION = "экскурсия"
    HOLIDAY = "праздник"
    CONCERT = "концерт"


class AgeLimit(str, Enum):
    ZERO_PLUS = "0+"
    SIX_PLUS = "6+"
    TWELVE_PLUS = "12+"
    SIXTEEN_PLUS = "16+"


class Event(BaseModel):
    title: str
    description: str
    start_date: date
    end_date: Optional[date] = None
    address: str
    lat: float
    lon: float
    category: Category
    age_limit: AgeLimit
    price: Optional[str] = None
    url: str
    source: str
