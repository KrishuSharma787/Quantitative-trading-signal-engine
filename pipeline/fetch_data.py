import yfinance as yf
import pandas as pd
from config import TICKERS, BENCHMARK, PERIOD, INTERVAL


def fetch_benchmark() -> pd.Series:
    """Fetch SPY closing prices for correlation calculation."""
    df = yf.download(BENCHMARK, period=PERIOD, interval=INTERVAL, progress=False)
    close = df["Close"]
    if hasattr(close, "squeeze"):
        close = close.squeeze()
    return close


def fetch_ticker(ticker: str, spy_close: pd.Series) -> pd.DataFrame:
    """Download OHLCV for one ticker and attach benchmark series."""
    raw = yf.download(ticker, period=PERIOD, interval=INTERVAL, progress=False)

    # Flatten MultiIndex columns produced by newer yfinance versions
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = [col[0] for col in raw.columns]

    raw.reset_index(inplace=True)
    raw["Ticker"] = ticker

    # Align SPY to same date index
    spy_aligned = spy_close.reset_index()
    spy_aligned.columns = ["Date", "SPY_Close"]
    spy_aligned["Date"] = pd.to_datetime(spy_aligned["Date"])
    raw["Date"]         = pd.to_datetime(raw["Date"])

    raw = raw.merge(spy_aligned, on="Date", how="left")
    return raw


def fetch_all_tickers(tickers: list = TICKERS) -> pd.DataFrame:
    """Fetch all tickers and return a single concatenated DataFrame."""
    print(f"📡 Fetching market data for: {', '.join(tickers)}")
    spy_close  = fetch_benchmark()
    all_frames = []

    for ticker in tickers:
        try:
            df = fetch_ticker(ticker, spy_close)
            all_frames.append(df)
            print(f"  ✓ {ticker}: {len(df)} rows")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")

    combined = pd.concat(all_frames, ignore_index=True)
    print(f"✅ Fetched {len(combined)} total rows\n")
    return combined
