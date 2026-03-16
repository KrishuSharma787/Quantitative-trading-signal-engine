import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def _get(key: str, fallback: str = "") -> str:
    """Read from Streamlit secrets (cloud) or .env (local)."""
    try:
        import streamlit as st
        return st.secrets.get(key, os.getenv(key, fallback))
    except Exception:
        return os.getenv(key, fallback)

# ── Tickers ────────────────────────────────────────────────
TICKERS    = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN"]
BENCHMARK  = "SPY"
PERIOD     = "6mo"
INTERVAL   = "1d"

# ── Database ───────────────────────────────────────────────
DB_PATH    = "stocks.db"

# ── Local CSV fallback paths (used before SQLite is seeded) ─
DATA_DIR          = "data"
CSV_STOCK         = "data/sample_stock_data.csv"
CSV_SP500         = "data/sp500_index_data.csv"
CSV_FINAL         = "data/final_analysis.csv"

# ── Refresh ────────────────────────────────────────────────
REFRESH_INTERVAL_MINUTES = 5

# ── News / Sentiment ───────────────────────────────────────
NEWS_API_KEY        = _get("NEWS_API_KEY")
NEWS_ARTICLES_LIMIT = 10

# ── ML ─────────────────────────────────────────────────────
ML_FEATURES  = ["RSI", "RSI_lag1", "SMA_cross", "Return_lag1", "Compound_avg"]
ML_TEST_SIZE = 0.2

# ── Alerts ─────────────────────────────────────────────────
ALERT_EMAIL_FROM     = _get("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO       = _get("ALERT_EMAIL_TO")
ALERT_EMAIL_PASSWORD = _get("ALERT_EMAIL_PASSWORD")
RSI_OVERBOUGHT       = 70
RSI_OVERSOLD         = 30
