"""
app.py — Streamlit frontend for the Quantitative Trading Signal Engine.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from database import read_df, get_connection
from config   import DB_PATH

st.set_page_config(
    page_title = "Quantitative Trading Signal Engine",
    page_icon  = "📈",
    layout     = "wide"
)

# ── Helpers ────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_stock(ticker: str) -> pd.DataFrame:
    return read_df(f"SELECT * FROM stock_data WHERE Ticker='{ticker}' ORDER BY Date")

@st.cache_data(ttl=300)
def load_sentiment(ticker: str) -> pd.DataFrame:
    return read_df(
        f"SELECT * FROM sentiment WHERE Ticker='{ticker}' ORDER BY Published DESC LIMIT 12"
    )

@st.cache_data(ttl=300)
def load_sentiment_summary(ticker: str) -> pd.DataFrame:
    return read_df(f"SELECT * FROM sentiment_summary WHERE Ticker='{ticker}'")

@st.cache_data(ttl=300)
def load_backtest(ticker: str) -> pd.DataFrame:
    return read_df(f"SELECT * FROM backtest_results WHERE Ticker='{ticker}'")

@st.cache_data(ttl=300)
def load_tickers() -> list:
    try:
        return read_df("SELECT DISTINCT Ticker FROM stock_data")["Ticker"].tolist()
    except Exception:
        return []

SIGNAL_COLORS = {
    "STRONG BUY":  "#2ecc71",
    "BUY":         "#82e0aa",
    "HOLD":        "#f0b429",
    "SELL":        "#f1948a",
    "STRONG SELL": "#e74c3c",
}

# ── Sidebar ────────────────────────────────────────────────────────────────────

st.sidebar.title("📈 Signal Engine")
st.sidebar.markdown("---")

tickers  = load_tickers()
if not tickers:
    st.error("⚠️  No data found. Please run `python run.py --once` first.")
    st.stop()

selected = st.sidebar.selectbox("Select Ticker", tickers)
st.sidebar.markdown("---")

df       = load_stock(selected)
if df.empty:
    st.warning(f"No data for {selected}")
    st.stop()

df["Date"] = pd.to_datetime(df["Date"])

# Date filter
min_date = df["Date"].min().date()
max_date = df["Date"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if len(date_range) == 2:
    df = df[(df["Date"].dt.date >= date_range[0]) &
            (df["Date"].dt.date <= date_range[1])]

# Show Bollinger Bands toggle
show_bb = st.sidebar.checkbox("Show Bollinger Bands", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("**Legend**")
for sig, col in SIGNAL_COLORS.items():
    st.sidebar.markdown(
        f"<span style='color:{col};font-weight:600'>■</span> {sig}",
        unsafe_allow_html=True
    )

# ── Header KPIs ───────────────────────────────────────────────────────────────

latest       = df.iloc[-1]
prev         = df.iloc[-2] if len(df) > 1 else latest
price_delta  = latest["Close"] - prev["Close"]
pct_delta    = (price_delta / prev["Close"]) * 100
signal       = latest.get("Signal_Label", "HOLD")
signal_color = SIGNAL_COLORS.get(signal, "#f0b429")

st.title(f"Quantitative Trading Signal Engine — {selected}")

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Current Price",  f"${latest['Close']:.2f}",   f"{pct_delta:+.2f}%")
k2.metric("Period High",    f"${df['High'].max():.2f}")
k3.metric("Period Low",     f"${df['Low'].min():.2f}")
k4.metric("Avg RSI",        f"{df['RSI'].mean():.1f}")
k5.metric("10D Correlation",f"{latest['10D_Corr']:.2f}" if pd.notna(latest['10D_Corr']) else "N/A")
k6.markdown(
    f"<div style='padding:8px 0'><span style='font-size:12px;color:#888'>ML Signal</span><br/>"
    f"<span style='font-size:22px;font-weight:700;color:{signal_color}'>{signal}</span></div>",
    unsafe_allow_html=True
)

st.markdown("---")

# ── Main layout: charts (left 2/3) + sentiment (right 1/3) ───────────────────

col_charts, col_sentiment = st.columns([2, 1])

# ── CHARTS ─────────────────────────────────────────────────────────────────────

with col_charts:

    # Price + SMA + Bollinger
    fig_price = go.Figure()

    if show_bb and "BB_Upper" in df.columns:
        fig_price.add_trace(go.Scatter(
            x=df["Date"], y=df["BB_Upper"], name="BB Upper",
            line=dict(color="#aab4be", width=1, dash="dot"), showlegend=True
        ))
        fig_price.add_trace(go.Scatter(
            x=df["Date"], y=df["BB_Lower"], name="BB Lower",
            line=dict(color="#aab4be", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(170,180,190,0.1)", showlegend=True
        ))

    fig_price.add_trace(go.Scatter(
        x=df["Date"], y=df["Close"], name="Price",
        line=dict(color="#1f77b4", width=2)
    ))
    fig_price.add_trace(go.Scatter(
        x=df["Date"], y=df["3D_SMA"], name="3D SMA",
        line=dict(color="#ff7f0e", width=1.5, dash="dot")
    ))
    fig_price.add_trace(go.Scatter(
        x=df["Date"], y=df["7D_SMA"], name="7D SMA",
        line=dict(color="#2ca02c", width=1.5, dash="dash")
    ))

    # Buy/sell signal markers
    buy_df  = df[df["Signal_Label"].isin(["BUY", "STRONG BUY"])]
    sell_df = df[df["Signal_Label"].isin(["SELL", "STRONG SELL"])]
    if not buy_df.empty:
        fig_price.add_trace(go.Scatter(
            x=buy_df["Date"], y=buy_df["Close"], mode="markers", name="Buy signal",
            marker=dict(symbol="triangle-up", size=10, color="#2ecc71")
        ))
    if not sell_df.empty:
        fig_price.add_trace(go.Scatter(
            x=sell_df["Date"], y=sell_df["Close"], mode="markers", name="Sell signal",
            marker=dict(symbol="triangle-down", size=10, color="#e74c3c")
        ))

    fig_price.update_layout(
        title=f"{selected} — Price & Moving Averages",
        height=320, margin=dict(t=40, b=20, l=0, r=0),
        legend=dict(orientation="h", y=-0.15)
    )
    st.plotly_chart(fig_price, use_container_width=True)

    # RSI
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=df["Date"], y=df["RSI"], name="RSI",
        line=dict(color="#9467bd", width=2),
        fill="tozeroy", fillcolor="rgba(148,103,189,0.1)"
    ))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",
                      annotation_text="Overbought (70)")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green",
                      annotation_text="Oversold (30)")
    fig_rsi.update_layout(
        title="Relative Strength Index (RSI)",
        height=220, yaxis_range=[0, 100],
        margin=dict(t=40, b=20, l=0, r=0)
    )
    st.plotly_chart(fig_rsi, use_container_width=True)

    # Backtest: portfolio vs buy-and-hold
    bt_summary = load_backtest(selected)
    if not bt_summary.empty:
        # Recompute portfolio curve from stock_data
        bt_df = df.copy()
        if "Portfolio_Value" not in bt_df.columns:
            # Rough reconstruction
            cash, shares = 10000.0, 0.0
            pv = []
            for _, row in bt_df.iterrows():
                if row.get("Signal_Label") in ("BUY","STRONG BUY") and cash > 0:
                    shares = cash / row["Close"]; cash = 0.0
                elif row.get("Signal_Label") in ("SELL","STRONG SELL") and shares > 0:
                    cash = shares * row["Close"]; shares = 0.0
                pv.append(cash + shares * row["Close"])
            bt_df["Portfolio_Value"] = pv
            bt_df["BuyHold_Value"]   = 10000 * (bt_df["Close"] / bt_df["Close"].iloc[0])

        fig_bt = go.Figure()
        fig_bt.add_trace(go.Scatter(
            x=bt_df["Date"], y=bt_df["Portfolio_Value"],
            name="ML Strategy", line=dict(color="#e67e22", width=2)
        ))
        fig_bt.add_trace(go.Scatter(
            x=bt_df["Date"], y=bt_df["BuyHold_Value"],
            name="Buy & Hold", line=dict(color="#3498db", width=2, dash="dot")
        ))
        row0 = bt_summary.iloc[0]
        alpha_str = f"+{row0['Alpha_Pct']:.1f}%" if row0['Alpha_Pct'] >= 0 else f"{row0['Alpha_Pct']:.1f}%"
        fig_bt.update_layout(
            title=f"Backtest: ML Strategy vs Buy & Hold (Alpha: {alpha_str})",
            height=240, margin=dict(t=40, b=20, l=0, r=0),
            legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig_bt, use_container_width=True)

# ── SENTIMENT PANEL ────────────────────────────────────────────────────────────

with col_sentiment:
    st.subheader("📰 Sentiment Analysis")

    summary = load_sentiment_summary(selected)

    if not summary.empty:
        row      = summary.iloc[0]
        score    = float(row["Avg_Compound"])
        mood     = str(row["Mood"])
        pos      = int(row["Positive_Count"])
        neg      = int(row["Negative_Count"])
        neu      = int(row["Neutral_Count"])
        total    = pos + neg + neu or 1

        # Gauge chart
        gauge_color = (
            "#2ecc71" if score > 0.05
            else "#e74c3c" if score < -0.05
            else "#f0b429"
        )
        fig_gauge = go.Figure(go.Indicator(
            mode  = "gauge+number",
            value = score,
            number= {"valueformat": ".3f", "font": {"size": 28}},
            gauge = {
                "axis":  {"range": [-1, 1], "tickwidth": 1},
                "bar":   {"color": gauge_color},
                "steps": [
                    {"range": [-1.0, -0.05], "color": "#fadbd8"},
                    {"range": [-0.05, 0.05], "color": "#f2f3f4"},
                    {"range": [ 0.05,  1.0], "color": "#d5f5e3"},
                ],
            },
            title = {"text": mood, "font": {"size": 14}}
        ))
        fig_gauge.update_layout(
            height=220,
            margin=dict(t=30, b=0, l=20, r=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Breakdown
        st.markdown("**Headline breakdown**")
        b1, b2, b3 = st.columns(3)
        b1.metric("🟢 Positive", pos)
        b2.metric("🔴 Negative", neg)
        b3.metric("⚪ Neutral",  neu)

        # Donut
        fig_donut = px.pie(
            names  = ["Positive", "Negative", "Neutral"],
            values = [pos, neg, neu],
            color  = ["Positive", "Negative", "Neutral"],
            color_discrete_map={
                "Positive": "#2ecc71",
                "Negative": "#e74c3c",
                "Neutral":  "#95a5a6"
            },
            hole=0.55
        )
        fig_donut.update_layout(
            height=200,
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    else:
        st.info("No sentiment data yet. Run the pipeline first.")

    # Headlines
    st.markdown("**Latest headlines**")
    headlines = load_sentiment(selected)

    if not headlines.empty:
        for _, row in headlines.iterrows():
            icon = {"Positive": "🟢", "Negative": "🔴", "Neutral": "⚪"}.get(
                row.get("Label", "Neutral"), "⚪"
            )
            headline = str(row.get("Headline", ""))[:70]
            url      = str(row.get("URL", "#"))
            source   = str(row.get("Source", ""))
            compound = float(row.get("Compound", 0))
            st.markdown(
                f"{icon} [{headline}...]({url})  \n"
                f"<span style='font-size:11px;color:#888'>"
                f"{source} &nbsp;·&nbsp; score: {compound:.3f}</span>",
                unsafe_allow_html=True
            )
            st.markdown("<hr style='margin:4px 0;border-color:#eee'>",
                        unsafe_allow_html=True)
    else:
        st.caption("No headlines available.")

# ── Cross-ticker comparison (full width) ──────────────────────────────────────

st.markdown("---")
st.subheader("🔀 Cross-Ticker Comparison")

c1, c2 = st.columns(2)

with c1:
    all_df = read_df("SELECT * FROM stock_data ORDER BY Date")
    all_df["Date"] = pd.to_datetime(all_df["Date"])

    fig_comp = go.Figure()
    for t in tickers:
        sub = all_df[all_df["Ticker"] == t].sort_values("Date")
        if sub.empty: continue
        fig_comp.add_trace(go.Scatter(
            x=sub["Date"], y=sub["Cumul_Growth"],
            name=t, mode="lines", line=dict(width=2)
        ))
    fig_comp.update_layout(
        title="Cumulative $1 Growth — All Tickers",
        height=300, margin=dict(t=40, b=20, l=0, r=0),
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with c2:
    try:
        bt_all = read_df("SELECT * FROM backtest_results")
        if not bt_all.empty:
            fig_alpha = go.Figure()
            colors    = [
                "#2ecc71" if v >= 0 else "#e74c3c"
                for v in bt_all["Alpha_Pct"]
            ]
            fig_alpha.add_trace(go.Bar(
                x=bt_all["Ticker"],
                y=bt_all["Alpha_Pct"],
                marker_color=colors,
                name="Alpha %"
            ))
            fig_alpha.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_alpha.update_layout(
                title="ML Strategy Alpha vs Buy & Hold",
                height=300, margin=dict(t=40, b=20, l=0, r=0)
            )
            st.plotly_chart(fig_alpha, use_container_width=True)
    except Exception:
        st.info("Run backtest to see alpha comparison.")

# ── Summary table ──────────────────────────────────────────────────────────────

try:
    bt_table = read_df("SELECT * FROM backtest_results")
    if not bt_table.empty:
        st.subheader("📋 Portfolio Summary")
        st.dataframe(
            bt_table.style.format({
                "Final_Portfolio":      "${:.2f}",
                "Final_BuyHold":        "${:.2f}",
                "Total_Return_Pct":     "{:.2f}%",
                "BuyHold_Return_Pct":   "{:.2f}%",
                "Alpha_Pct":            "{:+.2f}%",
            }).applymap(
                lambda v: "color: #2ecc71" if isinstance(v, float) and v > 0
                else ("color: #e74c3c" if isinstance(v, float) and v < 0 else ""),
                subset=["Alpha_Pct", "Total_Return_Pct"]
            ),
            use_container_width=True
        )
except Exception:
    pass

st.markdown(
    "<p style='text-align:center;color:#aaa;font-size:12px;margin-top:32px'>"
    "Quantitative Trading Signal Engine · Not financial advice</p>",
    unsafe_allow_html=True
)
