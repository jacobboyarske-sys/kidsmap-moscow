# KidsMap Moscow

Карта детских событий Москвы на [Streamlit](https://streamlit.io): фильтры по дате,
категории, возрасту и источнику, поиск по смыслу запроса и синхронизация карты
с таблицей.

🔗 **Приложение:** _добавьте сюда ссылку после деплоя на Streamlit Community Cloud_

## Возможности

- Карта событий (`folium`) с цветовой кодировкой по категориям, клик по точке
  фильтрует таблицу до выбранного события.
- Фильтры в сайдбаре: диапазон дат, категории, возраст, источник данных.
- Семантический поиск по смыслу запроса (`sentence-transformers`,
  `cointegrated/rubert-tiny2`) — например, «что-то спокойное для трёхлетки».
- Данные собираются автоматически с восьми источников (см. `data/sources.json`).

## Стек

Python 3.11+, Streamlit, folium/streamlit-folium, pandas, pydantic,
sentence-transformers, requests + BeautifulSoup4.

## Установка и запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows; на Linux/macOS — source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

## Сбор данных

```bash
python -m src.collect_events   # скрапинг всех источников, результат — data/events.json
python -m src.embed_events     # пересчёт эмбеддингов для семантического поиска
```

## Структура проекта

```
src/
├── app.py              # Streamlit-приложение
├── models.py            # pydantic-модель Event
├── data.py               # загрузка, фильтрация, де-дупликация событий
├── classify.py             # правила классификации по возрасту
├── collect_events.py        # оркестратор сбора данных со всех источников
├── embed_events.py           # предвычисление эмбеддингов для поиска
├── search.py                  # семантический поиск по эмбеддингам
└── scrapers/                   # по одному модулю на источник
data/
├── events.json           # рабочий датасет событий
├── seed_events.json       # вручную собранные события (стартовый набор)
├── sources.json             # список источников для скрапинга
└── geocode_cache.json        # кэш геокодирования площадок (Nominatim)
```

## Про проект

Это учебный pet-проект: код написан в паре с [Claude Code](https://claude.com/claude-code)
как инструментом обучения, а не автогенерации. Пошаговый план и заметки по решениям —
в [tutorials/README.md](tutorials/README.md), правила работы над проектом — в
[CLAUDE.md](CLAUDE.md).
