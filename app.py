# app.py  —  IPL Batters Dashboard (era‑adjusted with season filter)

import os
import streamlit as st
import pandas as pd
import altair as alt

# ─────────────────────────────────────────────────────────────
# 0. Page configuration
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IPL Batters – Era‑adjusted Stats",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# 1. Data loader (cached)
# ─────────────────────────────────────────────────────────────
DATA_PATH = "data/ipl_batter_metrics.parquet"

@st.cache_data
def load_metrics(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        st.error(
            f"❌ **{path}** not found. "
            "Run the preprocessing notebook or push the parquet file."
        )
        st.stop()
    return pd.read_parquet(path)

df = load_metrics(DATA_PATH)

# ─────────────────────────────────────────────────────────────
# 2. Sidebar — filters
# ─────────────────────────────────────────────────────────────
st.sidebar.header("Filters")

# Season multi‑select
seasons_all = sorted(df.season.dropna().unique())
seasons_sel = st.sidebar.multiselect(
    "Seasons (year)",
    seasons_all,
    default=seasons_all,
    help="Choose one or more IPL seasons to include in the analysis",
)

# Phase selector
phase = st.sidebar.selectbox("Phase", df.phase.unique())

# Overall career filters
min_runs  = st.sidebar.slider(
    "Min career runs", 0, int(df.total_runs.max()), 500, 100
)
min_games = st.sidebar.slider(
    "Min career matches", 0, int(df.games.max()), 25, 5
)

# How many top batters to show
top_n = st.sidebar.slider("Top‑N by Zulu", 5, 50, 25, 5)

# Scatter axis mode
axis_mode = st.sidebar.radio(
    "Scatter axes",
    ("Raw SR vs Avg", "True SR vs Avg"),
)

# ─────────────────────────────────────────────────────────────
# 3. Apply filters
# ─────────────────────────────────────────────────────────────
mask = (
    (df.phase == phase)
    & (df.season.isin(seasons_sel))
    & (df.total_runs >= min_runs)
    & (df.games >= min_games)
)

view = (
    df[mask]
    .sort_values("zulu", ascending=False)
    .head(top_n)
    .reset_index(drop=True)
)

# ─────────────────────────────────────────────────────────────
# 4. Display table
# ─────────────────────────────────────────────────────────────
st.subheader(
    f"{phase} – Top {len(view)} by Zulu  "
    f"({', '.join(map(str, seasons_sel))})"
)

st.dataframe(
    view[
        [
            "batter",
            "runs",
            "balls",
            "average",
            "strike_rate",
            "true_avg",
            "true_sr",
            "zulu",
            "games",
            "total_runs",
        ]
    ],
    use_container_width=True,
)

# ─────────────────────────────────────────────────────────────
# 5. Scatter plot
# ─────────────────────────────────────────────────────────────
if axis_mode.startswith("Raw"):
    x_col, y_col = "strike_rate", "average"
    x_lab, y_lab = "Strike‑rate", "Average"
else:
    x_col, y_col = "true_sr", "true_avg"
    x_lab, y_lab = "True SR (÷ era mean)", "True Avg (÷ era mean)"

base = (
    alt.Chart(view)
    .mark_circle(size=120, opacity=0.75, stroke="black")
    .encode(
        x=alt.X(f"{x_col}:Q", title=x_lab),
        y=alt.Y(f"{y_col}:Q", title=y_lab),
        tooltip=[
            "batter",
            "runs",
            "balls",
            "average",
            "strike_rate",
            "true_avg",
            "true_sr",
            "zulu",
            "games",
            "total_runs",
        ],
    )
)

labels = (
    alt.Chart(view)
    .mark_text(dy=-9, fontSize=10)
    .encode(x=f"{x_col}:Q", y=f"{y_col}:Q", text="batter")
)

st.altair_chart((base + labels).interactive(), use_container_width=True)

