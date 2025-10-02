# 💹 BTMM + Quarters AI Forex Signal Engine  

## 📖 Overview  
This project implements an **AI-assisted forex trading signal system** combining:  
- **Steve Mauro’s Beat The Market Maker (BTMM) Method**  
- **The Quarters Theory**  

The system ingests forex data (USD/MXN), applies BTMM + Quarters confluence rules, and generates **buy/sell signals** during **London** and **New York** sessions.  

It features **technical indicators (EMA, RSI, ATR, Quarters grid)**, **market sentiment analysis (PFH/PFL, levels, bias)**, and **AI-enhanced decision support** via a **vector database + LLM chat assistant**.  

---

## 🚀 Features  
- ✅ Real-time intraday data via **Yahoo Finance**  
- ✅ Session-based signal generation (London/NY)  
- ✅ Confluence logic: sweeps + RSI + EMA + Quarters  
- ✅ Signal scoring system for confidence weighting  
- ✅ Automated **email alerts with chart attachments**  
- ✅ Weekly **backtests with equity curve + KPIs**  
- ✅ **Market Sentiment Analysis** (PFH, PFL, Levels, Quarters, Bias)  
- ✅ **Streamlit Dashboard** with weekly trade log + charts  
- ✅ Interactive **LLM-powered Strategy Chat** (grounded in vector DB + last market snapshot)  

---

## 📂 Project Structure  
```text
btmm-qt-ai/
├── src/
│   ├── analyze_and_alert.py     # fetch data, compute signals, send alerts
│   ├── signal_engine.py         # signal rules (BTMM + Quarters confluence)
│   ├── feature_lab.py           # EMA, RSI, ATR, Quarters grid features
│   ├── sentiment.py             # PFH/PFL, levels, bias sentiment module
│   ├── chart_export.py          # exports trade chart w/ shaded sessions
│   ├── email_utils.py           # sends email alerts with attachments
│   ├── backtest.py              # runs backtests + KPIs
│   ├── utils_rag.py             # vector DB (FAISS) + retrieval helper
│   ├── spec_schema.py           # strategy schema (Pydantic)
│   ├── spec_from_docs.py        # parse PDFs into StrategySpec JSON
│   └── streamlit_app.py         # dashboard + AI chat interface
│
├── outputs/
│   ├── signals/                 # CSV signals
│   ├── alerts/                  # exported charts + last alert JSON
│   └── images/                  # screenshots for README
│
├── data/market/                 # saved historical bars
├── requirements.txt
├── README.md
└── .env.example
```
## 📊 Example Outputs
🔹 Weekly Dashboard
🔹 AI Strategy Chat

Interactive strategy chat box using your vector DB + OpenAI.
You can ask questions like:

“What’s the current bias?”

“How do BTMM levels align this week?”

“Where’s the best confluence for a short?”
![image](outputs\images\dash.png)
---
“Where’s the best confluence for a short?”

⚙️ How It Works

Fetch Data → From Yahoo Finance (15m, last 7 days).

Compute Features → EMA, RSI, ATR, Quarters, session tagging.

Signal Engine → Detects sweeps + confluence rules.

Scoring → Assigns confidence weights (0–100).

Sentiment Analysis → PFH/PFL, levels, quarter grid, bias.

Alerts → Sends email with trade signal + chart.

Streamlit Dashboard → Logs trades, visualizes signals.

LLM Chat Assistant → Retrieves knowledge from vector DB + last snapshot to answer strategic questions.

![image](outputs\images\test_chart.png)

# 🛠 Setup & Run
```bash
git clone https://github.com/mjcolon218/BTMM-QT-AI.git
cd BTMM-QT-AI
```
# Install Dependencies
```bash
pip install -r requirements.txt 
```
# Configure Environment
```bash
ALERT_TO=youremail@gmail.com
ALERT_FROM=youremail@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=youremail@gmail.com
SMTP_PASS=your_app_password
OPENAI_API_KEY=sk-xxxxx
```
# Run Analysis & Alerts
```bash
python src\analyze_and_alert.py
```
# Run in Test mode
```bash
python src\analyze_and_alert.py --test --signal BUY
```
# Run Backtest
```bash
python src\backtest.py
````
# Launch Dashboard
```bash
streamlit run src\streamlit_app.py
```

* Brought to you By Maurice J. Colon
2025