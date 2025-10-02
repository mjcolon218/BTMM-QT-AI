# streamlit_app.py
import streamlit as st
import pandas as pd
from src.sentiment import market_sentiment
from src.chart_export import export_trade_chart
from openai import OpenAI
import os
from src.utils_rag import retrieve_from_vector_db
import dotenv
dotenv.load_dotenv(override=True)

# Load API key (make sure it's in your .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
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
# Title
st.title("💬 USD/MXN Strategy Chat Assistant")

# Keep conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask about USD/MXN, signals, or BTMM strategy..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 📊 Context: latest market snapshot
    context = ""
    try:
        last_row = df.tail(1).to_dict(orient="records")[0]
        context = f"Latest signal snapshot: {last_row}"
    except:
        context = "No recent market data loaded."

    # 📚 Context: retrieved knowledge
    kb_context = "\n\n".join(retrieve_from_vector_db(prompt, k=5))

    # 🔗 Combined context
    system_context = (
        "You are a forex trading assistant using BTMM + Quarters Theory. "
        "Ground your answers in provided knowledge and recent data."
    )

    with st.chat_message("assistant"):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system", "content": system_context},
                    {"role":"system", "content": f"Knowledge base:\n{kb_context}"},
                    {"role":"system", "content": f"Market data:\n{context}"},
                    *st.session_state.messages
                ]
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error: {e}"

        st.markdown(reply)
    st.session_state.messages.append({"role":"assistant","content":reply})