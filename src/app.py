import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pydeck as pdk
import streamlit as st

from src.data import filter_events, load_events
from src.models import AgeLimit, Category
from src.search import load_embeddings, load_model, search_events


@st.cache_resource
def get_search_resources():
    try:
        model = load_model()
        embeddings, key_to_index = load_embeddings()
        return model, embeddings, key_to_index
    except FileNotFoundError:
        return None, None, None

st.set_page_config(layout="wide")
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
search_query = st.sidebar.text_input(
    "Поиск по смыслу", placeholder="например: что-то спокойное для трёхлетки"
)

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
        map_df = pd.DataFrame([e.model_dump() for e in filtered_events])
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            id="events",
            get_position=["lon", "lat"],
            get_fill_color=[220, 60, 60],
            get_radius=150,
            pickable=True,
            auto_highlight=True,
        )
        view_state = pdk.ViewState(latitude=55.75, longitude=37.62, zoom=9)
        deck = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=None,
            tooltip={"text": "{title}\n{address}"},
        )
        event = st.pydeck_chart(
            deck, on_select="rerun", selection_mode="single-object", key="map"
        )
        indices = event.selection.indices.get("events", [])
        if indices:
            selected_index = indices[0]
    else:
        st.write("Нет событий в выбранном диапазоне")

with col1:
    st.write(f"Событий в выбранном диапазоне: {len(filtered_events)}")

    table_columns = ["title", "start_date", "category", "age_limit", "price"]
    if filtered_events:
        df = pd.DataFrame([e.model_dump() for e in filtered_events])[table_columns]
        if selected_index is not None and selected_index in df.index:
            df = pd.concat([df.loc[[selected_index]], df.drop(selected_index)])

        def highlight_selected(row: pd.Series) -> list[str]:
            if selected_index is not None and row.name == selected_index:
                return ["background-color: #ffe08a"] * len(row)
            return [""] * len(row)

        st.dataframe(df.style.apply(highlight_selected, axis=1), hide_index=True)
    else:
        st.write("Нет событий в выбранном диапазоне")
