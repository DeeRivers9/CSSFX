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

# Timeframes and relaxed ADX threshold
timeframes = {
    "H1": {"interval": Interval.INTERVAL_1_HOUR, "adx_thresh": 10},
    "H4": {"interval": Interval.INTERVAL_4_HOURS, "adx_thresh": 10},
    "D1": {"interval": Interval.INTERVAL_1_DAY, "adx_thresh": 10}
}

currencies = list(set([cur for pair in pairs.values() for cur in pair]))

def get_adaptive_sar_trend(pair, interval, adx_threshold, tf_label, debug_logs):
    try:
        handler = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange="FX_IDC",
            interval=interval
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators
        summary = analysis.summary.get("RECOMMENDATION", "NEUTRAL")

        close = ind.get("close")
        sar = ind.get("SAR")
        adx = ind.get("ADX")

        if close is None or sar is None:
            debug_logs.append(f"{pair} ({tf_label}): Missing SAR/close → fallback to summary = {summary}")
            return summary

        if adx is not None and adx < adx_threshold:
            debug_logs.append(f"{pair} ({tf_label}): ADX={adx:.2f} < {adx_threshold} → NEUTRAL")
            return "NEUTRAL"

        if abs(close - sar) < 0.0001:
            debug_logs.append(f"{pair} ({tf_label}): Close≈SAR → fallback to summary = {summary}")
            return summary

        if close > sar:
            debug_logs.append(f"{pair} ({tf_label}): Close={close} > SAR={sar} → BUY")
            return "BUY"
        elif close < sar:
            debug_logs.append(f"{pair} ({tf_label}): Close={close} < SAR={sar} → SELL")
            return "SELL"
        else:
            debug_logs.append(f"{pair} ({tf_label}): Close={close}, SAR={sar} → NEUTRAL fallback")
            return summary
    except Exception as e:
        debug_logs.append(f"{pair} ({tf_label}): Exception → NEUTRAL ({e})")
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
st.title("📊 Currency Strength Matrix (Enhanced SAR Logic + Adaptive Sensitivity)")

results = {}
debug_output = []

# Calculate scores
for tf_label, tf_params in timeframes.items():
    scores = {c: 0 for c in currencies}
    for symbol, (base, quote) in pairs.items():
        signal = get_adaptive_sar_trend(symbol, tf_params["interval"], tf_params["adx_thresh"], tf_label, debug_output)
        update_scores(scores, base, quote, signal)
    df = pd.DataFrame(scores.items(), columns=["Currency", tf_label])
    results[tf_label] = df

# Merge and classify
final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Remarks"] = final_df.apply(get_remark, axis=1)

# Display result
st.dataframe(final_df, use_container_width=True)

# Debug info
with st.expander("🔍 Debug Logs (SAR, ADX, and Decision Paths)"):
    for line in debug_output:
        st.text(line)