import streamlit as st
from tradingview_ta import TA_Handler, Interval
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

# Detect trend using SAR + ADX
def get_sar_adx_trend(pair, interval):
    try:
        handler = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange="FX_IDC",
            interval=interval
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators

        close = ind.get("close", 0)
        sar = ind.get("SAR", 0)
        adx = ind.get("ADX", 0)

        if adx < 20:
            return "NEUTRAL"  # Weak trend = range
        elif close > sar:
            return "BUY"
        elif close < sar:
            return "SELL"
        else:
            return "NEUTRAL"
    except:
        return "NEUTRAL"

# Update currency scores
def update_scores(scores, base, quote, signal):
    if signal == "BUY":
        scores[base] += 1
        scores[quote] -= 1
    elif signal == "SELL":
        scores[base] -= 1
        scores[quote] += 1

# Determine remark based on all 3 timeframes
def get_remark(row):
    values = [row["H1"], row["H4"], row["D1"]]
    if all(-3 <= v <= 3 for v in values):
        return "NEUTRAL"
    elif any(v > 3 for v in values) and any(v < -3 for v in values):
        return "INVALID"
    else:
        return "NEUTRAL"

# Streamlit UI
st.title("📊 Currency Strength Matrix (SAR + ADX Trend Logic)")

results = {}

for tf_name, tf_interval in timeframes.items():
    scores = {c: 0 for c in currencies}
    for symbol, (base, quote) in pairs.items():
        signal = get_sar_adx_trend(symbol, tf_interval)
        update_scores(scores, base, quote, signal)
    df = pd.DataFrame(scores.items(), columns=["Currency", tf_name])
    results[tf_name] = df

# Merge and display
final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Remarks"] = final_df.apply(get_remark, axis=1)

st.dataframe(final_df, use_container_width=True)