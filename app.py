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

# Timeframes with individual ADX thresholds
timeframes = {
    "H1": {"interval": Interval.INTERVAL_1_HOUR, "adx_thresh": 20},
    "H4": {"interval": Interval.INTERVAL_4_HOURS, "adx_thresh": 15},
    "D1": {"interval": Interval.INTERVAL_1_DAY, "adx_thresh": 15}
}

currencies = list(set([cur for pair in pairs.values() for cur in pair]))

def get_sar_adx_trend(pair, interval, adx_threshold, tf_label, debug_logs):
    try:
        handler = TA_Handler(
            symbol=pair,
            screener="forex",
            exchange="FX_IDC",
            interval=interval
        )
        analysis = handler.get_analysis()
        ind = analysis.indicators

        close = ind.get("close", None)
        sar = ind.get("SAR", None)
        adx = ind.get("ADX", None)

        if close is None or sar is None or adx is None:
            signal = analysis.summary["RECOMMENDATION"]
            debug_logs.append(f"{pair} ({tf_label}): fallback to TV_TA summary = {signal}")
            return signal

        if adx < adx_threshold:
            debug_logs.append(f"{pair} ({tf_label}): ADX={adx} < {adx_threshold} → NEUTRAL")
            return "NEUTRAL"
        elif close > sar:
            debug_logs.append(f"{pair} ({tf_label}): ADX={adx}, Close={close} > SAR={sar} → BUY")
            return "BUY"
        elif close < sar:
            debug_logs.append(f"{pair} ({tf_label}): ADX={adx}, Close={close} < SAR={sar} → SELL")
            return "SELL"
        else:
            debug_logs.append(f"{pair} ({tf_label}): ADX={adx}, Close≈SAR → NEUTRAL")
            return "NEUTRAL"
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

# UI setup
st.title("📊 Currency Strength Matrix (SAR + ADX w/ Fallback & Debug)")

results = {}
debug_output = []

# Collect scores per timeframe
for tf_label, tf_params in timeframes.items():
    scores = {c: 0 for c in currencies}
    for symbol, (base, quote) in pairs.items():
        signal = get_sar_adx_trend(symbol, tf_params["interval"], tf_params["adx_thresh"], tf_label, debug_output)
        update_scores(scores, base, quote, signal)
    df = pd.DataFrame(scores.items(), columns=["Currency", tf_label])
    results[tf_label] = df

# Merge results and apply remark rules
final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Remarks"] = final_df.apply(get_remark, axis=1)

# Show result
st.dataframe(final_df, use_container_width=True)

# Optional debug output
with st.expander("🔍 Debug Logs (Indicator Values & Fallback Info)"):
    for line in debug_output:
        st.text(line)