import streamlit as st
import pandas as pd
import requests

API_KEY = "85aff05872a5422dbe962150c8d83ab8"

pairs = {
    "EUR/USD": ("EUR", "USD"),
    "GBP/USD": ("GBP", "USD"),
    "USD/JPY": ("USD", "JPY"),
    "AUD/USD": ("AUD", "USD"),
    "NZD/USD": ("NZD", "USD"),
    "USD/CAD": ("USD", "CAD"),
    "EUR/JPY": ("EUR", "JPY"),
    "EUR/GBP": ("EUR", "GBP"),
    "GBP/JPY": ("GBP", "JPY")
}

timeframes = {
    "H1": {"interval": "1h", "bars": 300},
    "H4": {"interval": "4h", "bars": 150},
    "D1": {"interval": "1day", "bars": 100}
}

sorted_currencies = ["AUD", "NZD", "JPY", "EUR", "GBP", "USD", "CAD"]

def fetch_candles(symbol, interval, limit):
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={limit}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.sort_values("datetime").astype({"high": float, "low": float, "close": float})
            return df.reset_index(drop=True)
    return None

def find_recent_swing(df, swing_window=3):
    highs = df["high"]
    lows = df["low"]
    swing_high_idx = None
    swing_low_idx = None

    for i in range(swing_window, len(df) - swing_window):
        is_high = all(highs[i] > highs[i - j] and highs[i] > highs[i + j] for j in range(1, swing_window + 1))
        is_low = all(lows[i] < lows[i - j] and lows[i] < lows[i + j] for j in range(1, swing_window + 1))

        if is_high:
            swing_high_idx = i
        if is_low:
            swing_low_idx = i

    if swing_high_idx is not None and swing_low_idx is not None:
        try:
            last_close = float(df["close"].iloc[-1])
            last_high = float(highs[swing_high_idx])
            last_low = float(lows[swing_low_idx])

            if last_close > last_high:
                return "BUY"
            elif last_close < last_low:
                return "SELL"
        except:
            return "NEUTRAL"
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
    if all(-3 <= v <= 3 for v in values):
        return "NEUTRAL"
    elif any(v > 3 for v in values) and any(v < -3 for v in values):
        return "INVALID"
    else:
        return "NEUTRAL"

# Streamlit App
st.title("📊 Currency Strength Matrix (Zigzag Swing Detection - Final Safe Fix)")

results = {}
debug_output = []

for tf_label, tf_info in timeframes.items():
    scores = {c: 0 for c in sorted_currencies}
    for symbol, (base, quote) in pairs.items():
        df = fetch_candles(symbol, tf_info["interval"], tf_info["bars"])
        signal = find_recent_swing(df)
        update_scores(scores, base, quote, signal)
        debug_output.append(f"{symbol} ({tf_label}): {signal}")
    df_result = pd.DataFrame(scores.items(), columns=["Currency", tf_label])
    results[tf_label] = df_result

# Merge and sort
final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Remarks"] = final_df.apply(get_remark, axis=1)
final_df["Currency"] = pd.Categorical(final_df["Currency"], categories=sorted_currencies, ordered=True)
final_df = final_df.sort_values("Currency")

st.dataframe(final_df, use_container_width=True)

with st.expander("🔍 Debug Logs (Zigzag Final Fix)"):
    for line in debug_output:
        st.text(line)