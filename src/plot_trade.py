# src/plot_trade.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def _scatter(ax, df, price_col, label, marker):
    """Plot markers only if there are rows."""
    if df.empty:
        return
    x = mdates.date2num(df.index.to_pydatetime())
    y = df[price_col].to_numpy(dtype=float)
    ax.scatter(x, y, marker=marker, s=60, label=label)

def plot_price_with_trades(df, price_col="Close", ema_col="EMA_21"):
    """
    Expects df with:
    - price_col (e.g., 'Close')
    - ema_col (e.g., 'EMA_21') if you want the overlay
    - TradeAction in {'BUY','SELL','EXIT-TP','EXIT-SL', None}
    Index must be DatetimeIndex (ns resolution is fine).
    """
    # Ensure DatetimeIndex
    if not df.index.inferred_type.startswith("datetime"):
        df = df.copy()
        df.index = pd.to_datetime(df.index)

    fig, ax = plt.subplots(figsize=(12, 5))

    # Plot price
    x_all = mdates.date2num(df.index.to_pydatetime())
    ax.plot(x_all, df[price_col].to_numpy(dtype=float), label=price_col)

    # Optional EMA overlay
    if ema_col in df.columns:
        ax.plot(x_all, df[ema_col].to_numpy(dtype=float), label=ema_col)

    # Subsets for markers
    buys     = df[df["TradeAction"] == "BUY"]
    sells    = df[df["TradeAction"] == "SELL"]
    exits_tp = df[df["TradeAction"] == "EXIT-TP"]
    exits_sl = df[df["TradeAction"] == "EXIT-SL"]

    # Scatter markers (guarded)
    _scatter(ax, buys,     price_col, "BUY",     "^")
    _scatter(ax, sells,    price_col, "SELL",    "v")
    _scatter(ax, exits_tp, price_col, "EXIT-TP", "o")
    _scatter(ax, exits_sl, price_col, "EXIT-SL", "x")

    # Pretty axis formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d\n%H:%M"))
    ax.set_title("Price with Trades")
    ax.grid(True)
    ax.legend()
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()
