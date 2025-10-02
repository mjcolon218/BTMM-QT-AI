# BTMM + Quarters AI Signal Engine

## 📖 Overview
This project implements an **AI-assisted forex trading signal system** that fuses:
- **Steve Mauro's Beat The Market Maker (BTMM) Method**
- **The Quarters Theory**

The system ingests forex data (USD/MXN), applies AI-enhanced strategies derived from your training documents (PDFs), and generates **buy/sell signals** during **London** and **New York** sessions.  

Features include:
- ✅ Historical data ingestion (Polygon API)  
- ✅ AI vector database for strategy rules  
- ✅ Signal engine with RSI, EMA, ATR, and Quarters grid logic  
- ✅ Backtesting with equity curve + KPIs  
- ✅ Chart generation (last 300 bars, markers, shaded London/NY)  
- ✅ Email alerts with signal details + chart attachment  
- ✅ Automated scheduling (Windows Task Scheduler)  
- ✅ *Optional Market Sentiment Analysis*: Summarizes peak formations, levels, and quarters at signal time  

---

## 🏗 Architecture

## 📂 Project Structure

```text
btmm-qt-ai/
├── src/
│   ├── analyze_and_alert.py     # main script to fetch data, analyze, and send alerts
│   ├── backtest_utils.py        # equity curve & KPIs
│   ├── chart_export.py          # export PNG charts w/ shaded sessions
│   ├── email_utils.py           # email sender w/ attachments
│   ├── feature_lab.py           # RSI, EMA, ATR, Quarters Grid
│   ├── signal_engine.py         # applies StrategySpec rules to data
│   ├── sentiment.py             # Market sentiment analysis (PFH/PFL, levels, quarters)
│   ├── spec_from_docs.py        # parses vectorized PDF knowledge into JSON spec
│   ├── test_chart.py            # test script to generate a chart
│   ├── test_email.py            # test script to send plain email
│   ├── test_email_chart.py      # test script to send chart as attachment
│
├── outputs/
│   ├── signals/                 # generated signal CSVs
│   └── alerts/                  # exported chart PNGs
│
├── requirements.txt
├── README.md
└── .env.example

