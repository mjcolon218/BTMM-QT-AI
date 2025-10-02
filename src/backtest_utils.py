# src/backtest_utils.py
import pandas as pd
import numpy as np

def equity_with_trades(df, atr_col="ATR_14", tp_rr=2.0, sl_atr_mult=1.5, init_equity=10000):
    """
    Simulates equity curve with simple fixed fraction risk model.
    df must already have 'Signal' column from signal_engine.
    Returns df with 'Equity' and 'TradeAction'.
    """
    eq = init_equity
    in_trade = False
    trade_side, entry_price, sl, tp = None, None, None, None
    actions, equities = [], []

    for i, row in df.iterrows():
        price = row["Close"]
        action = None

        if not in_trade:
            if row["Signal"] == "BUY":
                atr = row.get(atr_col, 0.001)
                sl = price - sl_atr_mult * atr
                tp = price + tp_rr * (price - sl)
                trade_side, entry_price = "LONG", price
                in_trade = True
                action = "BUY"
            elif row["Signal"] == "SELL":
                atr = row.get(atr_col, 0.001)
                sl = price + sl_atr_mult * atr
                tp = price - tp_rr * (sl - price)
                trade_side, entry_price = "SHORT", price
                in_trade = True
                action = "SELL"
        else:
            # Manage trade
            if trade_side == "LONG":
                if row["Low"] <= sl:  # hit stop
                    eq *= (1 - 0.01)  # lose 1%
                    in_trade, action = False, "EXIT-SL"
                elif row["High"] >= tp:  # hit TP
                    eq *= (1 + 0.02)  # win 2% (RR=2)
                    in_trade, action = False, "EXIT-TP"
            elif trade_side == "SHORT":
                if row["High"] >= sl:
                    eq *= (1 - 0.01)
                    in_trade, action = False, "EXIT-SL"
                elif row["Low"] <= tp:
                    eq *= (1 + 0.02)
                    in_trade, action = False, "EXIT-TP"

        actions.append(action)
        equities.append(eq)

    df["TradeAction"] = actions
    df["Equity"] = equities
    return df


def kpis(equity: pd.Series):
    """
    Simple KPIs from equity curve.
    """
    ret = equity.iloc[-1] / equity.iloc[0] - 1
    dd = (equity / equity.cummax() - 1).min()
    rets = equity.pct_change().dropna()
    sharpe = np.mean(rets) / (np.std(rets) + 1e-9) * np.sqrt(252*24*4)  # ~15-min bars
    return {"TotalReturn": ret, "Sharpe-ish": sharpe, "MaxDD": dd}
