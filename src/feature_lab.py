# src/feature_lab.py
import pandas as pd
import numpy as np

# -----------------
# RSI (Relative Strength Index)
# -----------------
def rsi(close, n=14):
    n = int(n)   # <-- force integer
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / (down + 1e-12)
    return 100 - (100 / (1 + rs))

def atr(df, n=14):
    n = int(n)   # <-- force integer
    hl = (df["High"] - df["Low"]).abs()
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(n).mean()
def ema(series: pd.Series, n: int = 14) -> pd.Series:
    """
    Exponential Moving Average
    series: price series (Close)
    n: lookback period
    """
    n = int(n)
    return series.ewm(span=n, adjust=False).mean()


def sma(series, n):
    n = int(n)   # <-- force integer
    return series.rolling(n).mean()

def quarter_grid(price, size_pips=25, pip_scale=0.0001):
    size_pips = int(size_pips)   # <-- also cast here
    pip_scale = float(pip_scale)
    grid = np.floor(price / (size_pips * pip_scale)) * (size_pips * pip_scale)
    dist = price - grid
    step = size_pips * pip_scale
    labels = ["Q1", "Q2", "Q3", "Q4"]
    idx = np.clip(np.floor(dist / step).astype(int), 0, 3)
    return pd.Series([labels[i] for i in idx], index=price.index, name="QG")
def quarter_distance_pips(close):
    # map to nearest 00/25/50/75 levels
    q = ((close*10000) % 2500)  # pip scale example, adjust for MXN decimals
    return np.minimum(q, 2500 - q) / 100  # distance in pips approx

def add_mtf_features(df):
    h1 = df[["Open","High","Low","Close"]].resample("60min").last()
    h1["EMA_50"] = h1["Close"].ewm(span=50, adjust=False).mean()
    h1["EMA_50_Slope"] = h1["EMA_50"].diff()
    df["H1_EMA_50_Slope"] = h1["EMA_50_Slope"].reindex(df.index, method="ffill")
    return df

def add_extras(df):
    df["RSI_14_prev"] = df["RSI_14"].shift(1)
    df["ATR_14_Pips"] = df["ATR_14"] * 100  # adjust pip factor per instrument
    df["QG_DistPips"] = quarter_distance_pips(df["Close"])
    return df
def sweep_flags(df, lookback=20, pad_pips=5):
    hh = df["High"].rolling(lookback).max().shift(1)
    ll = df["Low"].rolling(lookback).min().shift(1)
    took_high = df["High"] > (hh + pad_pips*1e-4)  # adjust pip scale if needed
    took_low  = df["Low"]  < (ll - pad_pips*1e-4)
    close_back_in_hi = took_high & (df["Close"] < hh)
    close_back_in_lo = took_low  & (df["Close"] > ll)
    df["SweepHi"] = close_back_in_hi.astype(int)
    df["SweepLo"] = close_back_in_lo.astype(int)
    return df
