import streamlit as st
import pandas as pd
import altair as alt
import os

# ─── page setup ─────────────────────────────────────────────
st.set_page_config(page_title="IPL Batters – Era-adjusted Stats",
                   layout="wide")

# ─── load data ──────────────────────────────────────────────
DATA_PATH = "data/ipl_batter_metrics.parquet"
if not os.path.isfile(DATA_PATH):
    st.error(f"{DATA_PATH} not found.  Run the preprocessing step first.")
    st.stop()

df = pd.read_parquet(DATA_PATH)

# ─── sidebar filters ────────────────────────────────────────
phase     = st.sidebar.selectbox("Phase", df.phase.unique())
min_runs  = st.sidebar.slider("Min career runs", 0,
                              int(df.total_runs.max()), 500, 100)
min_games = st.sidebar.slider("Min career matches", 0,
                              int(df.games.max()), 25, 5)
top_n     = st.sidebar.slider("Top-N by Zulu", 5, 50, 25, 5)
axis_mode = st.sidebar.radio("Scatter axes",
                             ("Raw SR vs Avg", "True SR vs Avg"))

# ─── filter & sort ──────────────────────────────────────────
view = (
    df[df.phase == phase]
    .query("total_runs >= @min_runs and games >= @min_games")
    .sort_values("zulu", ascending=False)
    .head(top_n)
    .reset_index(drop=True)
)

# ─── table ─────────────────────────────────────────────────
st.subheader(f"{phase} – Top {len(view)} by Zulu")
st.dataframe(
    view[["batter", "runs", "balls", "average", "strike_rate",
          "true_avg", "true_sr", "zulu", "games", "total_runs"]],
    use_container_width=True,
)

# ─── scatter plot ──────────────────────────────────────────
if axis_mode.startswith("Raw"):
    x_col, y_col = "strike_rate", "average"
    x_lab, y_lab = "Strike-rate", "Average"
else:
    x_col, y_col = "true_sr", "true_avg"
    x_lab, y_lab = "True SR (÷ era mean)", "True Avg (÷ era mean)"

base = alt.Chart(view).mark_circle(size=120, opacity=0.75, stroke="black").encode(
    x=alt.X(f"{x_col}:Q", title=x_lab),
    y=alt.Y(f"{y_col}:Q", title=y_lab),
    tooltip=["batter", "runs", "strike_rate", "average",
             "true_sr", "true_avg", "zulu"],
)

labels = alt.Chart(view).mark_text(dy=-9, fontSize=10).encode(
    x=f"{x_col}:Q",
    y=f"{y_col}:Q",
    text="batter"
)

st.altair_chart((base + labels).interactive(), use_container_width=True)
