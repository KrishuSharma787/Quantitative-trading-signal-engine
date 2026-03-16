import requests
import pandas as pd
import yfinance as yf
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from database import save_df, read_df
from config import NEWS_API_KEY, NEWS_ARTICLES_LIMIT, TICKERS

analyzer = SentimentIntensityAnalyzer()


def _label(compound: float) -> str:
    if compound >= 0.05:  return "Positive"
    if compound <= -0.05: return "Negative"
    return "Neutral"


def _mood(score: float) -> str:
    if score >= 0.15:   return "Very Bullish"
    if score >= 0.05:   return "Bullish"
    if score <= -0.15:  return "Very Bearish"
    if score <= -0.05:  return "Bearish"
    return "Neutral"


def fetch_newsapi(ticker: str) -> list:
    """Fetch headlines from NewsAPI (requires free API key)."""
    if not NEWS_API_KEY:
        return []
    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={ticker}&sortBy=publishedAt"
        f"&pageSize={NEWS_ARTICLES_LIMIT}&apiKey={NEWS_API_KEY}"
    )
    try:
        resp = requests.get(url, timeout=5)
        return resp.json().get("articles", [])
    except Exception as e:
        print(f"    NewsAPI error for {ticker}: {e}")
        return []


def fetch_yfinance_news(ticker: str) -> list:
    """Fallback: yfinance built-in news (no API key needed)."""
    articles = []
    try:
        for item in yf.Ticker(ticker).news[:5]:
            articles.append({
                "title":       item.get("title", ""),
                "publishedAt": datetime.fromtimestamp(
                    item.get("providerPublishTime", 0)
                ).isoformat(),
                "source":      {"name": item.get("publisher", "")},
                "url":         item.get("link", "")
            })
    except Exception as e:
        print(f"    yfinance news error for {ticker}: {e}")
    return articles


def score_articles(ticker: str, articles: list) -> list:
    results = []
    for art in articles:
        title = (art.get("title") or "").strip()
        if not title:
            continue
        scores   = analyzer.polarity_scores(title)
        compound = scores["compound"]
        results.append({
            "Ticker":    ticker,
            "Headline":  title,
            "Source":    art.get("source", {}).get("name", ""),
            "Published": art.get("publishedAt", ""),
            "URL":       art.get("url", ""),
            "Compound":  round(compound, 4),
            "Positive":  round(scores["pos"], 4),
            "Negative":  round(scores["neg"], 4),
            "Neutral":   round(scores["neu"], 4),
            "Label":     _label(compound),
            "FetchedAt": datetime.now().isoformat()
        })
    return results


def fetch_sentiment(ticker: str) -> list:
    articles  = fetch_newsapi(ticker) or fetch_yfinance_news(ticker)
    scored    = score_articles(ticker, articles)
    print(f"  ✓ {ticker}: {len(scored)} headlines scored")
    return scored


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = df.groupby("Ticker").apply(lambda x: pd.Series({
        "Avg_Compound":    round(x["Compound"].mean(), 4),
        "Positive_Count":  int((x["Label"] == "Positive").sum()),
        "Negative_Count":  int((x["Label"] == "Negative").sum()),
        "Neutral_Count":   int((x["Label"] == "Neutral").sum()),
        "Total_Articles":  len(x)
    })).reset_index()
    summary["Mood"] = summary["Avg_Compound"].apply(_mood)
    return summary


def run_sentiment_pipeline(tickers: list = TICKERS):
    print("📰 Running sentiment pipeline...")
    all_records = []
    for ticker in tickers:
        all_records.extend(fetch_sentiment(ticker))

    if not all_records:
        print("  ⚠️  No sentiment data retrieved")
        return

    df      = pd.DataFrame(all_records)
    summary = build_summary(df)

    save_df(df,      "sentiment",         if_exists="replace")
    save_df(summary, "sentiment_summary",  if_exists="replace")
    print(f"✅ Sentiment saved: {len(df)} records, {len(summary)} tickers\n")
