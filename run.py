"""
run.py — Main pipeline orchestrator.
Runs once immediately, then refreshes every N minutes.

Usage:
    python run.py            # run once + start scheduler
    python run.py --once     # run once and exit
"""

import sys
import schedule
import time
from datetime import datetime

from database          import init_db, save_df, read_df
from pipeline.fetch_data  import fetch_all_tickers
from pipeline.indicators  import process_all
from pipeline.sentiment   import run_sentiment_pipeline
from pipeline.ml_model    import run_ml_pipeline
from backtest.backtest    import run_backtest
from alerts.email_alerts  import check_and_alert
from config               import TICKERS, REFRESH_INTERVAL_MINUTES


def run_pipeline():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*55}")
    print(f"  Pipeline run started: {ts}")
    print(f"{'='*55}\n")

    # 1. Fetch raw OHLCV data
    raw_df = fetch_all_tickers(TICKERS)

    # 2. Compute technical indicators
    enriched_df = process_all(raw_df)

    # 3. Fetch & score news sentiment
    run_sentiment_pipeline(TICKERS)

    # 4. Train ML models + generate signals
    signal_df = run_ml_pipeline(enriched_df)

    # 5. Save master stock table
    cols_to_save = [
        "Date", "Ticker", "Open", "High", "Low", "Close", "Volume",
        "3D_SMA", "7D_SMA", "RSI", "Daily_Return", "Cumul_Growth",
        "SPY_Close", "10D_Corr", "ML_Signal", "Signal_Label",
        "BB_Upper", "BB_Mid", "BB_Lower"
    ]
    existing_cols = [c for c in cols_to_save if c in signal_df.columns]
    save_df(signal_df[existing_cols], "stock_data", if_exists="replace")
    print("✅ Stock data saved to database\n")

    # 6. Backtest signals
    run_backtest(signal_df)

    # 7. Email alerts
    latest = {}
    for ticker in TICKERS:
        sub = signal_df[signal_df["Ticker"] == ticker].sort_values("Date")
        if not sub.empty:
            latest[ticker] = sub.iloc[-1].to_dict()
    check_and_alert(latest)

    print(f"🏁 Pipeline complete — next run in {REFRESH_INTERVAL_MINUTES} min\n")


if __name__ == "__main__":
    init_db()
    run_pipeline()

    if "--once" not in sys.argv:
        schedule.every(REFRESH_INTERVAL_MINUTES).minutes.do(run_pipeline)
        print(f"🔄 Scheduler active ({REFRESH_INTERVAL_MINUTES}-min interval). "
              f"Press Ctrl+C to stop.\n")
        while True:
            schedule.run_pending()
            time.sleep(1)
