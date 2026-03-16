# 📈 Quantitative Trading Signal Engine

A real-time, end-to-end quantitative finance platform that ingests live stock data,
computes technical indicators, trains ML buy/sell signal classifiers augmented with
NLP sentiment analysis, backtests strategies, and visualises everything in an
interactive Streamlit web app.

---

## 🏗️ Architecture

```
yfinance / NewsAPI
       │
       ▼
  pipeline/
  ├── fetch_data.py      ← OHLCV ingestion for N tickers
  ├── indicators.py      ← RSI, SMA, Bollinger Bands, correlation
  ├── sentiment.py       ← VADER NLP scoring on news headlines
  └── ml_model.py        ← Logistic regression signal classifier
       │
       ▼
  SQLite database (stocks.db)
  ├── stock_data          ← enriched OHLCV + indicators + signals
  ├── sentiment           ← per-headline sentiment scores
  ├── sentiment_summary   ← per-ticker aggregate mood
  └── backtest_results    ← strategy vs buy-and-hold P&L
       │
       ├──▶  app.py        ← Streamlit web app (Plotly charts + sentiment sidebar)
       └──▶  Power BI      ← connected via SQLite ODBC driver
```

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Data ingestion | Python, yfinance, NewsAPI REST API |
| Data transformation | pandas, NumPy, vectorised rolling operations |
| NLP sentiment | VADER (vaderSentiment), NewsAPI |
| Machine learning | scikit-learn (LogisticRegression, StandardScaler) |
| Database | SQLite3 |
| Scheduling | schedule library |
| Web frontend | Streamlit, Plotly |
| BI dashboard | Power BI with DAX measures |
| Alerts | smtplib Gmail SMTP |

---

## 🚀 Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/KrishuSharma787/quantitative-trading-signal-engine
cd quantitative-trading-signal-engine
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your NewsAPI key and Gmail credentials
```

### 4. Run the pipeline (fetches data, trains model, runs backtest)
```bash
python run.py --once
```

### 5. Start the Streamlit app
```bash
streamlit run app.py
```

### 6. Auto-refresh every 5 minutes
```bash
python run.py   # runs pipeline on schedule, keep terminal open
```

---

## 📊 Features

### Technical Indicators
- 3-day and 7-day Simple Moving Averages (SMA)
- 14-day Relative Strength Index (RSI)
- 20-day Bollinger Bands (upper, mid, lower)
- 10-day rolling correlation vs S&P 500 (SPY benchmark)
- Daily % return and cumulative growth

### ML Signal Classifier
- **Model**: Logistic Regression (scikit-learn)
- **Features**: RSI, RSI lag-1, SMA crossover, lagged return, VADER compound score
- **Labels**: STRONG BUY / BUY / HOLD / SELL / STRONG SELL
- **Train/test split**: 80/20, chronological (no lookahead bias)

### NLP Sentiment Pipeline
- Sources: NewsAPI (primary) + yfinance built-in news (fallback)
- Scorer: VADER compound score per headline
- Aggregation: per-ticker average compound → Mood label
- Mood labels: Very Bullish / Bullish / Neutral / Bearish / Very Bearish
- Sentiment compound score used as ML feature

### Backtesting
- Starting capital: $10,000
- Strategy: go long on BUY/STRONG BUY, exit on SELL/STRONG SELL
- Benchmark: buy-and-hold from start of period
- Metrics: total return %, buy-hold return %, alpha, trade count

### Alerts
- Email via Gmail SMTP when RSI crosses overbought (>70) or oversold (<30)
- HTML-formatted email with ticker, price, RSI, and current ML signal

---

## 🧮 Key DAX Measures (Power BI)

```dax
Current Price = LASTNONBLANK(stock_data[Close], 1)

Period High = MAXX(FILTER(stock_data, stock_data[Ticker] = SELECTEDVALUE(stock_data[Ticker])), stock_data[High])

Avg RSI = AVERAGEX(stock_data, stock_data[RSI])

Last Signal = LASTNONBLANK(stock_data[Signal_Label], 1)

Chart Title = "Price & Moving Averages — " & SELECTEDVALUE(stock_data[Ticker], "All")
```

---

## 📸 Screenshots

> Add screenshots of your Streamlit app and Power BI dashboard here

---

## ⚠️ Disclaimer

This project is for educational purposes only. Nothing in this repository
constitutes financial advice. Past backtest performance does not guarantee
future results.
