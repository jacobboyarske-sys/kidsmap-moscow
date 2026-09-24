import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.data import filter_events, load_events
from src.models import AgeLimit, Category
from src.search import load_embeddings, load_model, search_events

CATEGORY_COLORS: dict[Category, str] = {
    Category.THEATRE: "#9c27b0",
    Category.WORKSHOP: "#ff9800",
    Category.QUEST: "#3f51b5",
    Category.SPORT: "#4caf50",
    Category.CINEMA: "#f44336",
    Category.EXCURSION: "#00bcd4",
    Category.HOLIDAY: "#ffc107",
    Category.CONCERT: "#1976d2",
}


@st.cache_resource
def get_search_resources():
    try:
        model = load_model()
        embeddings, key_to_index = load_embeddings()
        return model, embeddings, key_to_index
    except FileNotFoundError:
        return None, None, None

st.set_page_config(page_title="KidsMap Moscow", page_icon="🗺️", layout="wide")
st.title("KidsMap Moscow")

events = load_events()

today = date.today()
default_range = (today, today + timedelta(days=30))
date_range = st.sidebar.date_input("Диапазон дат", value=default_range)

if len(date_range) == 2:
    date_from, date_to = date_range
else:
    date_from, date_to = default_range

selected_categories = st.sidebar.multiselect(
    "Категории",
    options=list(Category),
    default=list(Category),
    format_func=lambda c: c.value,
)
selected_age_limits = st.sidebar.multiselect(
    "Возраст",
    options=list(AgeLimit),
    default=list(AgeLimit),
    format_func=lambda a: a.value,
)

st.sidebar.divider()

search_query = st.sidebar.text_input(
    "Поиск по смыслу", placeholder="например: что-то спокойное для трёхлетки"
)

st.sidebar.divider()

with st.sidebar.expander("Цвет на карте"):
    legend_html = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:2px;">'
        f'<span style="width:12px;height:12px;border-radius:2px;'
        f'background-color:{color};display:inline-block;"></span>'
        f"<span>{category.value}</span></div>"
        for category, color in CATEGORY_COLORS.items()
    )
    st.markdown(legend_html, unsafe_allow_html=True)

filtered_events = filter_events(
    events, date_from, date_to, selected_categories, selected_age_limits
)

if search_query.strip():
    model, embeddings, key_to_index = get_search_resources()
    if model is None:
        st.sidebar.warning(
            "Поиск по смыслу недоступен — сначала запустите `python -m src.embed_events`."
        )
    else:
        filtered_events = search_events(
            search_query, filtered_events, model, embeddings, key_to_index, top_n=10
        )

col1, col2 = st.columns(2)

selected_index = None

with col2:
    if filtered_events:
        m = folium.Map(location=[55.75, 37.62], zoom_start=9)
        location_lookup: dict[tuple[float, float, str], int] = {}
        for i, e in enumerate(filtered_events):
            color = CATEGORY_COLORS[e.category]
            folium.CircleMarker(
                location=[e.lat, e.lon],
                radius=12,
                color="white",
                weight=2,
                fill=True,
                fill_color=color,
                fill_opacity=0.9,
                tooltip=e.title,
                popup=f"{e.title}<br>{e.address}",
            ).add_to(m)
            location_lookup[(round(e.lat, 6), round(e.lon, 6), e.title)] = i

        lats = [e.lat for e in filtered_events]
        lons = [e.lon for e in filtered_events]
        m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

        map_data = st_folium(m, height=1000, use_container_width=True, key="map")

        clicked = map_data.get("last_object_clicked")
        clicked_tooltip = map_data.get("last_object_clicked_tooltip")
        if clicked and clicked_tooltip:
            key = (round(clicked["lat"], 6), round(clicked["lng"], 6), clicked_tooltip)
            selected_index = location_lookup.get(key)
    else:
        st.write("Нет событий в выбранном диапазоне")

with col1:
    st.write(f"Событий в выбранном диапазоне: {len(filtered_events)}")

    table_columns = ["start_date", "title", "category", "age_limit", "price", "url"]
    if filtered_events:
        df = pd.DataFrame([e.model_dump() for e in filtered_events])[table_columns]
        df = df.fillna("нет информации")
        if selected_index is not None and selected_index in df.index:
            df = pd.concat([df.loc[[selected_index]], df.drop(selected_index)])

        def highlight_selected(row: pd.Series) -> list[str]:
            if selected_index is not None and row.name == selected_index:
                return ["background-color: #ffe08a"] * len(row)
            return [""] * len(row)

        st.dataframe(
            df.style.apply(highlight_selected, axis=1),
            hide_index=True,
            height=800,
            column_config={
                "title": st.column_config.TextColumn("Название"),
                "start_date": st.column_config.DateColumn("Дата начала", format="DD.MM.YYYY"),
                "category": st.column_config.TextColumn("Категория"),
                "age_limit": st.column_config.TextColumn("Возраст"),
                "price": st.column_config.TextColumn("Цена"),
                "url": st.column_config.LinkColumn("Ссылка", display_text="Открыть"),
            },
        )
    else:
        st.write("Нет событий в выбранном диапазоне")
