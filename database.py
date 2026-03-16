import sqlite3
import pandas as pd
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_data (
            Date          TEXT,
            Ticker        TEXT,
            Open          REAL,
            High          REAL,
            Low           REAL,
            Close         REAL,
            Volume        REAL,
            "3D_SMA"      REAL,
            "7D_SMA"      REAL,
            RSI           REAL,
            Daily_Return  REAL,
            Cumul_Growth  REAL,
            SPY_Close     REAL,
            "10D_Corr"    REAL,
            ML_Signal     REAL,
            Signal_Label  TEXT,
            PRIMARY KEY (Date, Ticker)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sentiment (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            Ticker      TEXT,
            Headline    TEXT,
            Source      TEXT,
            Published   TEXT,
            URL         TEXT,
            Compound    REAL,
            Positive    REAL,
            Negative    REAL,
            Neutral     REAL,
            Label       TEXT,
            FetchedAt   TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sentiment_summary (
            Ticker          TEXT PRIMARY KEY,
            Avg_Compound    REAL,
            Positive_Count  INTEGER,
            Negative_Count  INTEGER,
            Neutral_Count   INTEGER,
            Total_Articles  INTEGER,
            Mood            TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS backtest_results (
            Ticker           TEXT PRIMARY KEY,
            Final_Portfolio  REAL,
            Final_BuyHold    REAL,
            Total_Return_Pct REAL,
            BuyHold_Return_Pct REAL,
            Alpha_Pct        REAL,
            Total_Trades     INTEGER
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialised")


def save_df(df: pd.DataFrame, table: str, if_exists: str = "replace"):
    conn = get_connection()
    df.to_sql(table, conn, if_exists=if_exists, index=False)
    conn.close()


def read_df(query: str) -> pd.DataFrame:
    conn = get_connection()
    df   = pd.read_sql(query, conn)
    conn.close()
    return df
