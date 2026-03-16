import pandas as pd
import numpy as np


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss  = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std: int = 2):
    sma   = series.rolling(period).mean()
    sigma = series.rolling(period).std()
    return sma + std * sigma, sma, sma - std * sigma


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all technical indicators to a single-ticker DataFrame."""
    df = df.copy().sort_values("Date").reset_index(drop=True)

    close = df["Close"].squeeze()

    df["3D_SMA"]       = close.rolling(3).mean()
    df["7D_SMA"]       = close.rolling(7).mean()
    df["RSI"]          = calculate_rsi(close)
    df["Daily_Return"] = close.pct_change() * 100
    df["Cumul_Growth"] = (1 + close.pct_change()).cumprod()
    df["10D_Corr"]     = close.rolling(10).corr(df["SPY_Close"].squeeze())

    bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(close)
    df["BB_Upper"] = bb_upper
    df["BB_Mid"]   = bb_mid
    df["BB_Lower"] = bb_lower

    return df


def process_all(combined: pd.DataFrame) -> pd.DataFrame:
    """Apply indicators to every ticker in the combined DataFrame."""
    frames = []
    for ticker in combined["Ticker"].unique():
        sub = combined[combined["Ticker"] == ticker].copy()
        sub = add_indicators(sub)
        frames.append(sub)
    result = pd.concat(frames, ignore_index=True)
    print("✅ Technical indicators calculated\n")
    return result
