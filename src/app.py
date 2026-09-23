import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import load_events

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

filtered_events = [e for e in events if date_from <= e.start_date <= date_to]

col1, col2 = st.columns(2)

with col1:
    st.write(f"Событий в выбранном диапазоне: {len(filtered_events)}")

    table_columns = ["title", "start_date", "category", "age_limit", "price"]
    if filtered_events:
        df = pd.DataFrame([e.model_dump() for e in filtered_events])[table_columns]
        st.dataframe(df, hide_index=True)
    else:
        st.write("Нет событий в выбранном диапазоне")

with col2:
    if filtered_events:
        map_df = pd.DataFrame([e.model_dump() for e in filtered_events])
        fig = px.scatter_map(
            map_df,
            lat="lat",
            lon="lon",
            hover_name="title",
            hover_data={"address": True, "lat": False, "lon": False},
            labels={"address": ""},
            zoom=9,
            center={"lat": 55.75, "lon": 37.62},
            height=500,
        )
        fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
        st.plotly_chart(fig)
    else:
        st.write("Нет событий в выбранном диапазоне")
