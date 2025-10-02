import yfinance as yf
import pandas as pd

def fetch_usdmxn_yf(interval="15m", period="7d"):
    """
    Fetch intraday USD/MXN candles using Yahoo Finance.
    interval: '1m','5m','15m','30m','60m','1d'
    period: '1d','5d','7d','1mo','3mo','6mo','1y'
    """
    ticker = "USDMXN=X"
    df = yf.download(ticker, interval=interval, period=period)

    if df.empty:
        raise RuntimeError("No data returned from Yahoo Finance")

    # Normalize columns
    df = df.rename(columns={
        "Open":"Open",
        "High":"High",
        "Low":"Low",
        "Close":"Close",
        "Volume":"Volume"
    })
    # Ensure UTC timezone
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")

    return df

if __name__ == "__main__":
    df = fetch_usdmxn_yf(interval="15m", period="7d")
    print("Data covers:", df.index.min(), "→", df.index.max())
    print(df.tail(10))  # show last 10 candles
