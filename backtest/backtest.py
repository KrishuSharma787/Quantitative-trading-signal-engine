import pandas as pd
import numpy as np
from database import save_df

INITIAL_CAPITAL = 10_000.0


def backtest_ticker(df: pd.DataFrame) -> dict:
    """
    Simulate trading on ML signals for one ticker.
    BUY / STRONG BUY  → go long (all-in)
    SELL / STRONG SELL → exit position
    HOLD               → maintain current state
    """
    df    = df.sort_values("Date").reset_index(drop=True)
    cash  = INITIAL_CAPITAL
    shares = 0.0
    trades = 0
    portfolio_values = []
    buyhold_values   = []

    start_price = df["Close"].iloc[0]

    for _, row in df.iterrows():
        price  = row["Close"]
        signal = row.get("Signal_Label", "HOLD")

        if signal in ("BUY", "STRONG BUY") and cash > 0:
            shares  = cash / price
            cash    = 0.0
            trades += 1

        elif signal in ("SELL", "STRONG SELL") and shares > 0:
            cash   = shares * price
            shares = 0.0
            trades += 1

        portfolio_values.append(cash + shares * price)
        buyhold_values.append(INITIAL_CAPITAL * (price / start_price))

    df["Portfolio_Value"] = portfolio_values
    df["BuyHold_Value"]   = buyhold_values

    final_portfolio = portfolio_values[-1]
    final_buyhold   = buyhold_values[-1]

    return {
        "df":                  df,
        "Final_Portfolio":     round(final_portfolio, 2),
        "Final_BuyHold":       round(final_buyhold, 2),
        "Total_Return_Pct":    round((final_portfolio / INITIAL_CAPITAL - 1) * 100, 2),
        "BuyHold_Return_Pct":  round((final_buyhold   / INITIAL_CAPITAL - 1) * 100, 2),
        "Alpha_Pct":           round(
            (final_portfolio - final_buyhold) / INITIAL_CAPITAL * 100, 2
        ),
        "Total_Trades":        trades
    }


def run_backtest(stock_df: pd.DataFrame) -> dict:
    """Run backtest for all tickers, save summary to DB, return per-ticker dfs."""
    print("📊 Running backtests...")
    results   = {}
    summaries = []

    for ticker in stock_df["Ticker"].unique():
        sub    = stock_df[stock_df["Ticker"] == ticker].copy()
        result = backtest_ticker(sub)

        results[ticker] = result["df"]

        summaries.append({
            "Ticker":              ticker,
            "Final_Portfolio":     result["Final_Portfolio"],
            "Final_BuyHold":       result["Final_BuyHold"],
            "Total_Return_Pct":    result["Total_Return_Pct"],
            "BuyHold_Return_Pct":  result["BuyHold_Return_Pct"],
            "Alpha_Pct":           result["Alpha_Pct"],
            "Total_Trades":        result["Total_Trades"]
        })

        alpha_str = (
            f"+{result['Alpha_Pct']:.2f}%" if result["Alpha_Pct"] >= 0
            else f"{result['Alpha_Pct']:.2f}%"
        )
        print(
            f"  ✓ {ticker}: "
            f"strategy {result['Total_Return_Pct']:+.1f}% | "
            f"buy-hold {result['BuyHold_Return_Pct']:+.1f}% | "
            f"alpha {alpha_str} | "
            f"{result['Total_Trades']} trades"
        )

    summary_df = pd.DataFrame(summaries)
    save_df(summary_df, "backtest_results", if_exists="replace")
    print("✅ Backtest complete\n")
    return results
