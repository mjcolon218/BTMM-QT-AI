# src/analyze_and_alert.py
import os, json, re, smtplib, requests
import pandas as pd
import yfinance as yf
import numpy as np
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import argparse
import pytz
# Local imports
from spec_schema import StrategySpec
from signal_engine import signalize
from feature_lab import ema, rsi, atr, quarter_grid
from sentiment import market_sentiment
from chart_export import export_trade_chart   # <--- NEW
def parse_args():
    parser = argparse.ArgumentParser(description="BTMM Quarters AI Signal Engine.")
    parser.add_argument("--test", action="store_true", help="Run in test mode(Force Signal)")
    parser.add_argument("--signal", choices=["BUY","SELL"], help="Forced Signal for test mode")
    return parser.parse_args()
# ---------- ENV ----------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
POLY_KEY       = os.getenv("POLYGON_API_KEY")
ALERT_TO       = os.getenv("ALERT_TO")
ALERT_FROM     = os.getenv("ALERT_FROM")
SMTP_HOST      = os.getenv("SMTP_HOST")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER      = os.getenv("SMTP_USER")
SMTP_PASS      = os.getenv("SMTP_PASS")

# ---------- HELPERS ----------
def utc_now():
    return datetime.now(timezone.utc)

def fetch_usdmxn_period(interval="15m", period="7d"):
    """
    Fetch intraday USD/MXN candles from Yahoo Finance.
    Flattens MultiIndex so downstream feature funcs work.
    """
    ticker = "USDMXN=X"
    df = yf.download(ticker, interval=interval, period=period)

    if df.empty:
        raise RuntimeError("No data returned from Yahoo Finance")

    # Flatten if yfinance gives MultiIndex (Price/Ticker)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    # Ensure UTC tz
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    # Keep consistent col order
    df = df[["Open","High","Low","Close","Volume"]]

    return df

def add_sessions(df):
    """
    Tag sessions using strict UTC hours:
    - Asia:   00:00–06:59 UTC
    - London: 07:00–11:59 UTC
    - NY:     12:00–16:59 UTC
    - Other:  all else
    """
    # Ensure all timestamps are in UTC
    idx_utc = (df.index.tz_localize("UTC") if df.index.tz is None else df.index.tz_convert("UTC"))
    hrs = idx_utc.hour

    sess = pd.cut(
        hrs,
        bins=[-1, 6, 11, 16, 23],
        labels=["Asia", "London", "NY", "Other"],
        right=True
    ).astype(str)

    out = df.copy()
    out["Session"] = sess
    return out




def read_cached_spec(path="outputs/specs/usdmxn_from_ai.json"):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return StrategySpec.model_validate_json(f.read())
    with open("outputs/specs/usdmxn_quarters_bmm.json", "r", encoding="utf-8") as f:
        return StrategySpec.model_validate_json(f.read())

def last_alert_path():
    os.makedirs("outputs/alerts", exist_ok=True)
    return "outputs/alerts/last_alert.json"

def already_alerted_for(timestamp_iso: str):
    p = last_alert_path()
    if not os.path.exists(p): return False
    try:
        d = json.load(open(p,"r",encoding="utf-8"))
        return d.get("last_bar") == timestamp_iso
    except Exception:
        return False

def write_last_alert(timestamp_iso: str, payload: dict):
    json.dump({"last_bar": timestamp_iso, "payload": payload}, open(last_alert_path(),"w",encoding="utf-8"), indent=2)

def send_email(subject: str, body: str, attachment=None):
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = ALERT_FROM
    msg["To"] = ALERT_TO
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))

    if attachment and os.path.exists(attachment):
        with open(attachment, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(attachment)}"')
        msg.attach(part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        if SMTP_USER and SMTP_PASS:
            s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(ALERT_FROM, [ALERT_TO], msg.as_string())

# Add confidence scoring
def score_signal(r):
    score = 0
    if r.get("SweepLo",0)==1 or r.get("SweepHi",0)==1: score += 40
    if r.get("QG_DistPips",99) <= 6: score += 20
    if r.get("RSI_14",0) < 30 or r.get("RSI_14",0) > 70: score += 20
    if (r.get("EMA_50",0) > r.get("EMA_200",0)) or (r.get("EMA_50",0) < r.get("EMA_200",0)): score += 20
    return score

# ---------- MAIN ----------
def main():
    args = parse_args()
    # 1) Data
    df = fetch_usdmxn_period(period="7d",interval="15m")
    df = add_sessions(df)

    last = df.index[-1]
    print("local time:", last.tz_convert("America/New_York"))
    print("UTC time:  ", last.tz_convert("UTC"))
    print("Session:   ", df.iloc[-1]["Session"])
   
    # 2) Strategy spec
    try:
        spec = read_cached_spec()
    except Exception:
        print("Spec load failed.")
        return

    # 3) Signals
    df = signalize(df, spec)
    print(df.head())
    if "Score" not in df.columns:
        df["Score"] = df.apply(score_signal, axis=1)
    if "EMA_50" not in df.columns:
        df["EMA_50"] = ema(df["Close"], 50)
    if "EMA_200" not in df.columns:
        df["EMA_200"] = ema(df["Close"], 200)

    cols = ["Close", "Signal", "Session","QG", "RSI_14", "EMA_50", "EMA_200","High","Low","SweepHi","SweepLo"]
    valid_cols = [c for c in cols if c in df.columns]
    out = df[valid_cols].copy()
    out['Score'] = df.apply(score_signal, axis=1)
    out.to_csv("outputs/signals/usdmxn_signals_with_trades.csv", index_label="Datetime")
    df.to_csv("data/market/USDMXN_M15.csv", index_label="Datetime")
    #print(df.tail(10)[["Close","Signal","Session","Score"]])
    #print(df.head())
    if df.empty:
        print("No data after dropna; exiting.")
        return

    # 4) Latest bar
    latest_dt = df.index[-1]
    latest = df.iloc[-1]
    score = latest.get("Score",0)
    #body += f"\nSignal confidence score: {score}/100\n"
    session = latest.get("Session","Other")
    signal  = latest.get("Signal","FLAT")
    if args.test:
        print(f"⚠️ Running in TEST MODE — forcing {args.signal}")
        signal = args.signal or "BUY"
        session = "London"

    if not args.test:
        if session not in ("London","NY"):
            print(f"Session={session}, skip.")
            
        elif signal not in ("BUY","SELL"):
            print(f"Signal={signal}, skip.")
            

    ts_iso = latest_dt.isoformat()
    if already_alerted_for(ts_iso):
        print("Already alerted for this bar; skip.")
        

    # 5) Sentiment analysis
    sentiment = market_sentiment(df)
    #print("Debug Sentiment:", sentiment)
    sentiment_str = "\n".join([f"- {k}: {v}" for k,v in sentiment.items()])
    
    #print(sentiment_str)

    # 6) Build alert body
    price = float(latest["Close"])
    qg    = latest.get("QG","?")
    rsi14 = latest.get("RSI_14", np.nan)
    ema21 = latest.get("EMA_50", np.nan)

    body = (
        f"USDMXN {signal} signal\n"
        f"Time (UTC): {latest_dt}\n"
        f"Session: {session}\n"
        f"Close: {price}\n"
        f"QG: {qg} | RSI_14: {rsi14:.2f} | EMA_50: {ema21:.5f}\n"
        f"Strategy: {spec.name}\n"
        f"Timeframe: {spec.timeframe}\n"
        f"Confidence Score: {score}/100\n"
        f"(Generated from BTMM + Quarters context)\n\n"
        "Market Sentiment:\n" + sentiment_str
    )
    subject = f"[USDMXN {spec.timeframe}] {signal} @ {price:.5f} ({session})"

    # 7) Export chart with sentiment
    chart_path = export_trade_chart(df, "outputs/images/usdmxn_chart.png", price_col="Close", ema_col="EMA_50", sentiment=sentiment)

    # 8) Send email
    if (session in ("London","NY")) and (signal in ("BUY","SELL")):
        send_email(subject, body, attachment=chart_path)
        if not args.test:
            write_last_alert(ts_iso, {"signal": signal, "price": price, "session": session})
        print("✅ Alert sent with sentiment + chart.")
    else:
        print("No alert window; Session = {session}, Signal = {signal}")
if __name__ == "__main__":
    main()
    
 