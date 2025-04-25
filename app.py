import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Parameters
pairs = {
    "EURUSD=X": ("EUR", "USD"),
    "GBPUSD=X": ("GBP", "USD"),
    "USDJPY=X": ("USD", "JPY"),
    "AUDUSD=X": ("AUD", "USD"),
    "NZDUSD=X": ("NZD", "USD"),
    "USDCAD=X": ("USD", "CAD"),
    "EURJPY=X": ("EUR", "JPY"),
    "EURGBP=X": ("EUR", "GBP"),
    "GBPJPY=X": ("GBP", "JPY")
}

timeframes = {
    "H1": {"interval": "1h", "period": "2d", "lookback": 5},
    "H4": {"interval": "1h", "period": "3d", "lookback": 12},
    "D1": {"interval": "1d", "period": "10d", "lookback": 3}
}

currencies = list(set([cur for pair in pairs.values() for cur in pair]))

def detect_trend(data, lookback):
    try:
        close_now = data["Close"].iloc[-1]
        close_past = data["Close"].iloc[-lookback]
        change_pct = (close_now - close_past) / close_past * 100

        if change_pct > 0.15:
            return "BUY"
        elif change_pct < -0.15:
            return "SELL"
        else:
            return "NEUTRAL"
    except:
        return "NEUTRAL"

def update_scores(scores, base, quote, signal):
    if signal == "BUY":
        scores[base] += 1
        scores[quote] -= 1
    elif signal == "SELL":
        scores[base] -= 1
        scores[quote] += 1

def get_remark(row):
    values = [row["H1"], row["H4"], row["D1"]]
    if all(v > 0 for v in values) or all(v < 0 for v in values) or all(v == 0 for v in values):
        return "NEUTRAL"
    else:
        return "INVALID"

# App UI
st.title("📈 Currency Strength Matrix (Line Chart Trend-Based)")

results = {}

for tf_name, tf_params in timeframes.items():
    scores = {c: 0 for c in currencies}

    for symbol, (base, quote) in pairs.items():
        data = yf.download(symbol, interval=tf_params["interval"], period=tf_params["period"], progress=False)
        signal = detect_trend(data, tf_params["lookback"])
        update_scores(scores, base, quote, signal)

    df = pd.DataFrame(scores.items(), columns=["Currency", tf_name])
    results[tf_name] = df

# Merge timeframes
final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Remarks"] = final_df.apply(get_remark, axis=1)

st.dataframe(final_df, use_container_width=True)