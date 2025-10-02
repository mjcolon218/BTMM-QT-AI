# src/analyze_and_alert.py
import os, json, re, smtplib, requests
import pandas as pd
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
ALPHA_KEY      = os.getenv("ALPHA_KEY")  # <-- NEW
# ---------- HELPERS ----------
def utc_now():
    return datetime.now(timezone.utc)

def fetch_usdmxn_period(interval="15min", outputsize="compact"):
    """
    Fetch USDMXN intraday candles from AlphaVantage.
    interval: '1min', '5min', '15min', '30min', '60min'
    outputsize: 'compact' (100 bars) or 'full' (~1 month)
    """
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": "USD",
        "to_symbol": "MXN",
        "interval": interval,
        "outputsize": outputsize,
        "apikey": ALPHA_KEY,  # <-- store in .env as ALPHA_KEY
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()

    if "Time Series FX (" not in str(js):
        raise RuntimeError(f"AlphaVantage response error: {js}")

    # Key looks like: "Time Series FX (15min)"
    ts_key = [k for k in js.keys() if "Time Series FX" in k][0]
    df = pd.DataFrame.from_dict(js[ts_key], orient="index")
    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close"
    }).astype(float)

    # Convert index to datetime (UTC)
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.sort_index()

    print("Data covers:", df.index.min(), "→", df.index.max())
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

# ---------- MAIN ----------
def main():
    args = parse_args()
    # 1) Data
    df = fetch_usdmxn_period()
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
        f"QG: {qg} | RSI_14: {rsi14:.2f} | EMA_50: {ema21:.5f}\n"
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
    
 