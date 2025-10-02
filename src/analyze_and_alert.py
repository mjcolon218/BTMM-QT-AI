# src/analyze_and_alert.py
import os, json, re, smtplib, requests
import pandas as pd
import numpy as np
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import argparse
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

def fetch_usdmxn_period(days=7, multiplier=15, timespan="minute"):
    end = utc_now().date()
    start = end - timedelta(days=days)
    url = f"https://api.polygon.io/v2/aggs/ticker/C:USDMXN/range/{multiplier}/{timespan}/{start}/{end}"
    r = requests.get(url, params={"adjusted":"true","sort":"asc","limit":50000,"apiKey":POLY_KEY}, timeout=30)
    r.raise_for_status()
    js = r.json()
    if "results" not in js:
        raise RuntimeError(f"Polygon response missing results: {js}")
    df = pd.DataFrame(js["results"])
    df["Datetime"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    df = df.rename(columns={"o":"Open","h":"High","l":"Low","c":"Close","v":"Volume"})
    df = df.set_index("Datetime")[["Open","High","Low","Close","Volume"]].sort_index()
    return df

def add_sessions(df):
    hrs = df.index.hour
    df["Session"] = pd.cut(
        hrs, bins=[-1, 6, 11, 16, 23],
        labels=["Asia","London","NY","Other"]
    ).astype(str)
    return df

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

# ---------- MAIN ----------
def main():
    args = parse_args()
    # 1) Data
    df = fetch_usdmxn_period(days=7)
    df = add_sessions(df)

    # 2) Strategy spec
    try:
        spec = read_cached_spec()
    except Exception:
        print("Spec load failed.")
        return

    # 3) Signals
    df = signalize(df, spec).dropna()
    if df.empty:
        print("No data after dropna; exiting.")
        return

    # 4) Latest bar
    latest_dt = df.index[-1]
    latest = df.iloc[-1]
    session = latest.get("Session","Other")
    signal  = latest.get("Signal","FLAT")
    if args.test:
        print(f"⚠️ Running in TEST MODE — forcing {args.signal}")
        signal = args.signal or "BUY"
        session = "London"

    if not args.test:
        if session not in ("London","NY"):
            print(f"Session={session}, skip.")
            return
        if signal not in ("BUY","SELL"):
            print(f"Signal={signal}, skip.")
            return

    ts_iso = latest_dt.isoformat()
    if already_alerted_for(ts_iso):
        print("Already alerted for this bar; skip.")
        return

    # 5) Sentiment analysis
    sentiment = market_sentiment(df)
    sentiment_str = "\n".join([f"- {k}: {v}" for k,v in sentiment.items()])

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
        f"QG: {qg} | RSI_14: {rsi14:.2f} | EMA_21: {ema21:.5f}\n"
        f"Strategy: {spec.name}\n"
        f"Timeframe: {spec.timeframe}\n"
        f"(Generated from BTMM + Quarters context)\n\n"
        "Market Sentiment:\n" + sentiment_str
    )
    subject = f"[USDMXN {spec.timeframe}] {signal} @ {price:.5f} ({session})"

    # 7) Export chart with sentiment
    chart_path = export_trade_chart(df, "outputs/alerts/usdmxn_chart.png", price_col="Close", ema_col="EMA_50", sentiment=sentiment)

    # 8) Send email
    send_email(subject, body, attachment=chart_path)
    if not args.test:
        write_last_alert(ts_iso, {"signal": signal, "price": price, "session": session})
    print("✅ Alert sent with sentiment + chart.")

if __name__ == "__main__":
    main()
