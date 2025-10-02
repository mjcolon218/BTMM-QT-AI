# src/signal_engine.py
import pandas as pd
from feature_lab import rsi, atr, sma, ema, quarter_grid, add_mtf_features, add_extras, quarter_distance_pips, sweep_flags
from spec_schema import StrategySpec

# Step 1: Add indicators from spec
def add_features(df, spec):
    out = df.copy()

    for ind in spec.indicators:
        alias = ind.alias or f"{ind.name}_{ind.params.get('period','')}"

        if ind.name == "RSI":
            out[alias] = rsi(out["Close"], ind.params.get("period", 14))
        elif ind.name == "EMA":
            out[alias] = ema(out["Close"], ind.params.get("period", 21))
        elif ind.name == "ATR":
            out[alias] = atr(out, ind.params.get("period", 14))
        elif ind.name == "QuarterGrid":
            out[alias] = quarter_grid(out["Close"])
        elif ind.name == "SMA":
            out[alias] = out["Close"].rolling(int(ind.params.get("period", 14))).mean()
        elif ind.name == "MACD":
            fast = ind.params.get("fast", 12)
            slow = ind.params.get("slow", 26)
            signal = ind.params.get("signal", 9)
            ema_fast = ema(out["Close"], fast)
            ema_slow = ema(out["Close"], slow)
            macd_line = ema_fast - ema_slow
            signal_line = ema(macd_line, signal)
            out[alias+"_line"] = macd_line
            out[alias+"_signal"] = signal_line

    # 🔹 Ensure ATR_14 always exists for extras
    if "ATR_14" not in out.columns:
        out["ATR_14"] = atr(out, 14)

    # Add extras
    out = add_extras(out)
    out = add_mtf_features(out)
    out = sweep_flags(out, lookback=20, pad_pips=5)

    return out



      # stop-hunt detector
    
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

        # --- BTMM Confluence Logic ---
        if (r.get("SweepLo",0)==1) and (r.get("RSI_14",0) > 30) and (r.get("QG_DistPips",99) <= 6) and (r.get("EMA_50",0) > r.get("EMA_200",0)):
            tag = "BUY"
        elif (r.get("SweepHi",0)==1) and (r.get("RSI_14",0) < 70) and (r.get("QG_DistPips",99) <= 6) and (r.get("EMA_50",0) < r.get("EMA_200",0)):
            tag = "SELL"

        # --- Spec-driven Entries ---
        else:
            for er in spec.entries:
                if safe_eval(r, er.condition):
                    tag = "BUY" if er.side == "LONG" else "SELL"
                    break

        signals.append(tag)

    df["Signal"] = signals
    return df

def confluence_buy(row):
    near_q = row["QG_DistPips"] <= 6  # within 6 pips of Q level
    rsi_ok = (row["RSI_14"] > 30) & (row["RSI_14_prev"] <= 30)  # rebound from oversold
    trend  = (row["EMA_50"] > row["EMA_200"]) & (row["H1_EMA_50_Slope"] > 0)
    vola   = (row["ATR_14_Pips"].between(5, 40))
    return near_q & rsi_ok & trend & vola

def confluence_sell(row):
    near_q = row["QG_DistPips"] <= 6
    rsi_ok = (row["RSI_14"] < 70) & (row["RSI_14_prev"] >= 70)  # roll from overbought
    trend  = (row["EMA_50"] < row["EMA_200"]) & (row["H1_EMA_50_Slope"] < 0)
    vola   = (row["ATR_14_Pips"].between(5, 40))
    return near_q & rsi_ok & trend & vola

