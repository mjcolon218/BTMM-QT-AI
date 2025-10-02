# src/signal_engine.py
import pandas as pd
from feature_lab import rsi, atr, sma, ema, quarter_grid
from spec_schema import StrategySpec

# Step 1: Add indicators from spec
def add_features(df, spec: StrategySpec):
    out = df.copy()
    for ind in spec.indicators:
        alias = ind.alias
        p = ind.params
        if ind.name == "RSI":
            out[alias] = rsi(out["Close"], p.get("period",14))
        if ind.name == "ATR":
            out[alias] = atr(out, p.get("period",14))
        if ind.name == "SMA":
            out[alias] = sma(out["Close"], p.get("period",50))
        if ind.name == "EMA":
            out[alias] = ema(out["Close"], p.get("period",21))
        if ind.name == "QuarterGrid":
            out["QG"] = quarter_grid(out["Close"], 
                                     p.get("size_pips",25), 
                                     p.get("pip_scale",0.0001))
    return out

# Step 2: Safe eval with Session support
def safe_eval(row, expr):
    """
    Evaluates strategy conditions like:
    (RSI_14 < 35) and (Close > EMA_21) and (QG == 'Q1') and (Session == 'London')
    """
    env = {k: row[k] for k in row.index if k not in ["Open","High","Low","Close","Volume"]}
    env.update({
        "Close": row["Close"],
        "Session": row.get("Session","")   # <-- add session into env
    })
    try:
        return bool(eval(expr, {"__builtins__": {}}, env))
    except Exception as e:
        return False

# Step 3: Apply entry rules → produce signals
def signalize(df, spec: StrategySpec):
    df = add_features(df, spec)
    signals = []
    for _, r in df.iterrows():
        tag = "FLAT"
        for er in spec.entries:
            if safe_eval(r, er.condition):
                tag = "BUY" if er.side == "LONG" else "SELL"
                break
        signals.append(tag)
    df["Signal"] = signals
    return df
