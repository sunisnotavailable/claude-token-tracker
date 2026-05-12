import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent / "token_usage.db"

st.set_page_config(page_title="Token Usage Dashboard", layout="wide")
st.title("Token 消耗监控")


@st.cache_data(ttl=30)
def load_data():
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM usage ORDER BY ts DESC", conn)
    conn.close()
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"])
    df["date"] = df["ts"].dt.date
    df["total_tok"] = df["input_tok"] + df["output_tok"]
    return df


df = load_data()

if df.empty:
    st.info("暂无数据。启动 proxy.py 并通过它发几次请求后刷新此页面。")
    st.stop()

# ── 顶部指标卡 ──────────────────────────────────────────
now = pd.Timestamp.now()
today_cost = df[df["date"] == now.date()]["total_tok"].sum()
week_cost = df[df["ts"] >= now - pd.Timedelta(days=7)]["total_tok"].sum()
month_cost = df[df["ts"] >= now - pd.Timedelta(days=30)]["total_tok"].sum()
total_calls = len(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("今日 token", f"{today_cost:,}")
col2.metric("近7天 token", f"{week_cost:,}")
col3.metric("近30天 token", f"{month_cost:,}")
col4.metric("总调用次数", f"{total_calls}")

st.divider()

# ── 每日趋势 ────────────────────────────────────────────
st.subheader("每日消耗趋势")
daily = df.groupby("date").agg(
    total_tokens=("total_tok", "sum"),
    input_tokens=("input_tok", "sum"),
    output_tokens=("output_tok", "sum"),
    calls=("id", "count"),
).reset_index()

col_a, col_b = st.columns(2)
with col_a:
    st.caption("总 token 数 / 天")
    st.line_chart(daily.set_index("date")["total_tokens"], height=250)
with col_b:
    st.caption("输入 vs 输出 token / 天")
    st.line_chart(daily.set_index("date")[["input_tokens", "output_tokens"]], height=250)

st.divider()

# ── 按模型分布 ──────────────────────────────────────────
st.subheader("按模型分布")
by_model = df.groupby("model").agg(
    调用次数=("id", "count"),
    总token=("total_tok", "sum"),
).sort_values("总token", ascending=False).reset_index()
st.dataframe(by_model, use_container_width=True, hide_index=True)

st.divider()

# ── 调用明细 ────────────────────────────────────────────
st.subheader("调用明细（最近 200 条）")
st.dataframe(
    df[["ts", "model", "input_tok", "output_tok", "total_tok", "project"]].head(200),
    use_container_width=True,
    hide_index=True,
)
