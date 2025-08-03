# app.py — IPL Batters Dashboard 

import streamlit as st
import pandas as pd
import altair as alt
import os


# Page & theme

st.set_page_config(
    page_title="IPL Batters – Era‑adjusted Stats",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Data loader (cached)

DATA_PATH = "data/ipl_batter_metrics.parquet"

@st.cache_data
def load_metrics(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        st.error(f"❌ {path} not found. Please run preprocessing first.")
        st.stop()
    return pd.read_parquet(path)

df = load_metrics(DATA_PATH)


# Sidebar filters

st.sidebar.header("Filters")

phase = st.sidebar.selectbox("Phase", df.phase.unique())
min_runs = st.sidebar.slider("Min career runs", 0, int(df.total_runs.max()), 500, 100)
min_games = st.sidebar.slider("Min career matches", 0, int(df.games.max()), 25, 5)
top_n = st.sidebar.slider("Top‑N by Zulu", 5, 50, 25, 5)
axis_mode = st.sidebar.radio("Scatter axes", ("Raw SR vs Avg", "True SR vs Avg"))


# Filter & sort

view = (
    df[df.phase == phase]
    .query("total_runs >= @min_runs and games >= @min_games")
    .sort_values("zulu", ascending=False)
    .head(top_n)
    .reset_index(drop=True)
)


# Table

st.subheader(f"{phase} – Top {len(view)} by Zulu")
st.dataframe(
    view[[
        "batter", "runs", "balls", "average", "strike_rate",
        "true_avg", "true_sr", "zulu", "games", "total_runs"
    ]],
    use_container_width=True,
)


# Scatter plot

if axis_mode.startswith("Raw"):
    x_col, y_col = "strike_rate", "average"
    x_lab, y_lab = "Strike-rate", "Average"
else:
    x_col, y_col = "true_sr", "true_avg"
    x_lab, y_lab = "True SR (÷ era mean)", "True Avg (÷ era mean)"

base = (
    alt.Chart(view)
    .mark_circle(size=120, opacity=0.75, stroke="black")
    .encode(
        x=alt.X(f"{x_col}:Q", title=x_lab),
        y=alt.Y(f"{y_col}:Q", title=y_lab),
        tooltip=["batter", "runs", "strike_rate", "average",
                 "true_sr", "true_avg", "zulu"],
    )
)

labels = (
    alt.Chart(view)
    .mark_text(dy=-9, fontSize=10)
    .encode(x=f"{x_col}:Q", y=f"{y_col}:Q", text="batter")
)

st.altair_chart((base + labels).interactive(), use_container_width=True)

