import streamlit as st
from tradingview_ta import TA_Handler, Interval
import pandas as pd

pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "EURJPY", "EURGBP", "GBPJPY"]
timeframes = {
    "H1": Interval.INTERVAL_1_HOUR,
    "H4": Interval.INTERVAL_4_HOURS,
    "D1": Interval.INTERVAL_1_DAY
}
currencies = ["EUR", "GBP", "USD", "JPY", "AUD", "NZD", "CAD"]

def update_scores(scores, base, quote, signal):
    if signal == "BUY":
        scores[base] += 1
        scores[quote] -= 1
    elif signal == "SELL":
        scores[base] -= 1
        scores[quote] += 1

def get_remark(score):
    if score >= 2:
        return "STRONG"
    elif score <= -2:
        return "WEAK"
    else:
        return "NEUTRAL"

st.title("📊 Currency Strength Matrix (Auto Trend Based)")

results = {}
for tf_name, tf_interval in timeframes.items():
    scores = {c: 0 for c in currencies}
    for pair in pairs:
        try:
            handler = TA_Handler(
                symbol=pair,
                screener="forex",
                exchange="FX_IDC",
                interval=tf_interval
            )
            analysis = handler.get_analysis()
            signal = analysis.summary["RECOMMENDATION"]
            base, quote = pair[:3], pair[3:]
            update_scores(scores, base, quote, signal)
        except:
            continue
    df = pd.DataFrame(scores.items(), columns=["Currency", tf_name])
    results[tf_name] = df

final_df = results["H1"].merge(results["H4"], on="Currency").merge(results["D1"], on="Currency")
final_df["Total"] = final_df[["H1", "H4", "D1"]].sum(axis=1)
final_df["Remarks"] = final_df["Total"].apply(get_remark)

st.dataframe(final_df, use_container_width=True)
