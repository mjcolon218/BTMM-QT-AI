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
