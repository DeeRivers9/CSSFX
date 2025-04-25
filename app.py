import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Your API key from TwelveData
API_KEY = "85aff05872a5422dbe962150c8d83ab8"

# Define pairs and mapping
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

# Timeframes settings
timeframes = {
    "H1": {"interval": "1h"},
    "H4": {"interval": "4h"},
    "D1": {"interval": "1day"}
}

# ADX thresholds per timeframe
adx_thresholds = {
    "H1": 20,
    "H4": 15,
    "D1": 10
}

# SAR buffer per timeframe
sar_buffers = {
    "H1": 0.0001,
    "H4": 0.0003,
    "D1": 0.0001
}

# Sorted currency order
sorted_currencies = ["AUD", "NZD", "JPY", "EUR", "GBP", "USD", "CAD"]

def fetch_indicator(symbol, interval, indicator):
    url = f"https://api.twelvedata.com/{indicator}?symbol={symbol}&interval={interval}&apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "values" in data:
            return pd.DataFrame(data["values"])
    return None

def get_signal(symbol, tf_label, debug_logs):
    interval = timeframes[tf_label]["interval"]
    adx_thresh = adx_thresholds[tf_label]
    sar_buffer = sar_buffers[tf_label]

    try:
        # Fetch latest SAR
        sar_df = fetch_indicator(symbol, interval, "sar")
        # Fetch latest ADX
        adx_df = fetch_indicator(symbol, interval, "adx")
        # Fetch latest price
        price_url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={API_KEY}"
        price_response = requests.get(price_url)
        close_price = float(price_response.json().get("price", 0))

        if sar_df is None or adx_df is None or close_price == 0:
            debug_logs.append(f"{symbol} ({tf_label}): Missing data → NEUTRAL")
            return "NEUTRAL"

        latest_sar = float(sar_df.iloc[0]["sar"])
        latest_adx = float(adx_df.iloc[0]["adx"])

        if latest_adx < adx_thresh:
            debug_logs.append(f"{symbol} ({tf_label}): ADX={latest_adx:.2f} < {adx_thresh} → NEUTRAL")
            return "NEUTRAL"

        if abs(close_price - latest_sar) < sar_buffer:
            debug_logs.append(f"{symbol} ({tf_label}): |Close - SAR|={abs(close_price - latest_sar):.5f} < {sar_buffer} → fallback NEUTRAL")
            return "NEUTRAL"

        if close_price > latest_sar:
            debug_logs.append(f"{symbol} ({tf_label}): Close={close_price} > SAR={latest_sar} → BUY")
            return "BUY"
        elif close_price < latest_sar:
            debug_logs.append(f"{symbol} ({tf_label}): Close={close_price} < SAR={latest_sar} → SELL")
            return "SELL"
        else:
            debug_logs.append(f"{symbol} ({tf_label}): Close≈SAR → fallback NEUTRAL")
            return "NEUTRAL"

    except Exception as e:
        debug_logs.append(f"{symbol} ({tf_label}): Exception → NEUTRAL ({e})")
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

# Streamlit app
st.title("📊 Currency Strength Matrix (TwelveData SAR + ADX Logic)")

results = {}
debug_output = []

for tf_label in timeframes.keys():
    scores = {c: 0 for c in sorted_currencies}
    for symbol, (base, quote) in pairs.items():
        signal = get_signal(symbol, tf_label, debug_output)
        update_scores(scores, base, quote, signal)
    df = pd.DataFrame(scores.items(), columns=["Currency", tf_label])
    results[tf_label] = df

# Merge and reorder
final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Remarks"] = final_df.apply(get_remark, axis=1)
final_df["Currency"] = pd.Categorical(final_df["Currency"], categories=sorted_currencies, ordered=True)
final_df = final_df.sort_values("Currency")

st.dataframe(final_df, use_container_width=True)

with st.expander("🔍 Debug Logs"):
    for line in debug_output:
        st.text(line)