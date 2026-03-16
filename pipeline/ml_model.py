import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from database import read_df, save_df
from config import ML_FEATURES, ML_TEST_SIZE


def build_features(df: pd.DataFrame, sentiment_summary: pd.DataFrame) -> pd.DataFrame:
    """Engineer ML features for a single ticker."""
    df = df.copy().sort_values("Date").reset_index(drop=True)

    df["RSI_lag1"]    = df["RSI"].shift(1)
    df["SMA_cross"]   = df["3D_SMA"] - df["7D_SMA"]
    df["Return_lag1"] = df["Daily_Return"].shift(1)

    # Merge avg sentiment compound score per ticker
    if not sentiment_summary.empty:
        df = df.merge(
            sentiment_summary[["Ticker", "Avg_Compound"]].rename(
                columns={"Avg_Compound": "Compound_avg"}
            ),
            on="Ticker", how="left"
        )
    else:
        df["Compound_avg"] = 0.0

    # Target: 1 if next day close is higher
    df["Target"] = (df["Close"].shift(-1) > df["Close"]).astype(int)

    return df


def train_ticker_model(df: pd.DataFrame):
    """Train logistic regression for one ticker. Returns (model, scaler, accuracy)."""
    features = [f for f in ML_FEATURES if f in df.columns]
    clean    = df.dropna(subset=features + ["Target"])

    if len(clean) < 30:
        return None, None, None

    X = clean[features].values
    y = clean["Target"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=ML_TEST_SIZE, shuffle=False
    )

    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    model   = LogisticRegression(max_iter=500)
    model.fit(X_train, y_train)

    acc = accuracy_score(y_test, model.predict(X_test))
    return model, scaler, acc


def add_signals(df: pd.DataFrame, model, scaler, features: list) -> pd.DataFrame:
    """Append ML_Signal and Signal_Label columns to df."""
    available = [f for f in features if f in df.columns]
    clean     = df.dropna(subset=available)

    if clean.empty or model is None:
        df["ML_Signal"]    = np.nan
        df["Signal_Label"] = "HOLD"
        return df

    X_scaled           = scaler.transform(clean[available].values)
    preds              = model.predict(X_scaled)
    proba              = model.predict_proba(X_scaled)[:, 1]

    df.loc[clean.index, "ML_Signal"]    = preds
    df.loc[clean.index, "Signal_Label"] = np.where(
        proba >= 0.60, "STRONG BUY",
        np.where(preds == 1, "BUY",
        np.where(proba <= 0.40, "STRONG SELL", "SELL"))
    )
    df["Signal_Label"].fillna("HOLD", inplace=True)
    return df


def run_ml_pipeline(stock_df: pd.DataFrame) -> pd.DataFrame:
    """Train per-ticker models, attach signals, print accuracy report."""
    print("🤖 Running ML signal pipeline...")

    try:
        sentiment_summary = read_df("SELECT * FROM sentiment_summary")
    except Exception:
        sentiment_summary = pd.DataFrame()

    all_frames = []
    features   = [f for f in ML_FEATURES if f != "Compound_avg"] + ["Compound_avg"]

    for ticker in stock_df["Ticker"].unique():
        sub = stock_df[stock_df["Ticker"] == ticker].copy()
        sub = build_features(sub, sentiment_summary)

        model, scaler, acc = train_ticker_model(sub)

        if model:
            print(f"  ✓ {ticker}: accuracy = {acc:.2%}")
            sub = add_signals(sub, model, scaler, features)
        else:
            print(f"  ⚠️  {ticker}: insufficient data for training")
            sub["ML_Signal"]    = np.nan
            sub["Signal_Label"] = "HOLD"

        all_frames.append(sub)

    result = pd.concat(all_frames, ignore_index=True)
    print("✅ ML signals generated\n")
    return result
