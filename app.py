import streamlit as st
from tradingview_ta import TA_Handler, Interval, Exchange
import pandas as pd

# Define currency pairs
pairs = {
    "EURUSD": ("EUR", "USD"),
    "GBPUSD": ("GBP", "USD"),
    "USDJPY": ("USD", "JPY"),
    "AUDUSD": ("AUD", "USD"),
    "NZDUSD": ("NZD", "USD"),
    "USDCAD": ("USD", "CAD"),
    "EURJPY": ("EUR", "JPY"),
    "EURGBP": ("EUR", "GBP"),
    "GBPJPY": ("GBP", "JPY")
}

# Define timeframes
timeframes = {
    "H1": Interval.INTERVAL_1_HOUR,
    "H4": Interval.INTERVAL_4_HOURS,
    "D1": Interval.INTERVAL_1_DAY
}

currencies = list(set([cur for pair in pairs.values() for cur in pair]))

def get_signal(pair, interval):
    try:
        handler = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange="FX_IDC",
            interval=interval
        )
        summary = handler.get_analysis().summary["RECOMMENDATION"]
        return summary
    except:
        return "NEUTRAL"

def update_scores(scores, base, quote, signal):
    if signal == "BUY":
        scores[base] += 1
        scores[quote] -= 1
    elif signal == "SELL":
        scores[base] -= 1
        scores[quote] += 1
    # NEUTRAL = no change

def get_remark(row):
    values = [row["H1"], row["H4"], row["D1"]]
    if all(-3 <= v <= 3 for v in values):
        return "NEUTRAL"
    elif (max(values) > 3 or min(values) < -3):
        if any(v > 3 for v in values) and any(v < -3 for v in values):
            return "INVALID"
        elif abs(max(values) - min(values)) > 6:
            return "INVALID"
        else:
            return "NEUTRAL"
    else:
        return "INVALID"

# Streamlit UI
st.title("📊 Currency Strength Matrix (Powered by TradingView TA)")

results = {}

for tf_name, tf_interval in timeframes.items():
    scores = {c: 0 for c in currencies}
    for symbol, (base, quote) in pairs.items():
        signal = get_signal(symbol, tf_interval)
        update_scores(scores, base, quote, signal)
    df = pd.DataFrame(scores.items(), columns=["Currency", tf_name])
    results[tf_name] = df

# Merge results
final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Remarks"] = final_df.apply(get_remark, axis=1)

st.dataframe(final_df, use_container_width=True)