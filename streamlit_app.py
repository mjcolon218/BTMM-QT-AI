# streamlit_app.py
import streamlit as st
import pandas as pd
from src.sentiment import market_sentiment
from src.chart_export import export_trade_chart

# Load last week's signals
df = pd.read_csv("outputs/signals/usdmxn_signals_with_trades.csv",parse_dates=["Datetime"])
df = df.set_index("Datetime")
st.title("📊 USDMXN BTMM + Quarters Dashboard")

# --- Weekly Stats ---
st.subheader("Weekly Signal Summary")
weekly = df.last("7D")
st.metric("Total Trades", len(weekly[weekly["Signal"].isin(["BUY","SELL"])]))
st.metric("Buys", len(weekly[weekly["Signal"]=="BUY"]))
st.metric("Sells", len(weekly[weekly["Signal"]=="SELL"]))

st.dataframe(weekly[["Signal","Session","Close","RSI_14","EMA_50","QG"]].tail(20))

# --- Market Sentiment ---
st.subheader("Market Sentiment Analysis")
sent = market_sentiment(df)
for k,v in sent.items():
    st.write(f"**{k}**: {v}")

# --- Chart ---
st.subheader("Recent Chart with Trades")
chart_path = export_trade_chart(df, "outputs/alerts/streamlit_chart.png", sentiment=sent)
st.image(chart_path, caption="Last 300 bars with signals & sentiment")

# --- Narrative Breakdown ---
st.subheader("AI Breakdown")
desc = (
    f"Current sentiment suggests price is in **{sent['Level']}** "
    f"after a {sent['PF']}. Bias is **{sent['Bias']}** "
    f"around quarter level {sent['Quarter']}."
)
st.write(desc)
