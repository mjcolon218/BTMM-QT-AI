# src/chart_export.py
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def export_trade_chart(df, fname="outputs/alerts/trade_chart.png",
                       price_col="Close", ema_col="EMA_50",
                       sentiment=None):
    """
    Save a PNG of the last ~300 bars with BUY/SELL/EXIT markers,
    shading London & NY sessions, and adding sentiment text if provided.
    """

    #os.makedirs(os.path.dirname(fname), exist_ok=True)

    df_last = df.tail(300).copy()
    if df_last.empty or price_col not in df_last.columns:
        raise ValueError("DataFrame empty or missing price column for chart export.")

    fig, ax = plt.subplots(figsize=(12, 6))
    x_all = mdates.date2num(df_last.index.to_pydatetime())

    # Price + EMA
    ax.plot(x_all, df_last[price_col], label=price_col, color="black", linewidth=1.2)
    if ema_col in df_last.columns:
        ax.plot(x_all, df_last[ema_col], label=ema_col, color="blue", linewidth=1.0)

    # Shading sessions (London/NY)
    if "Session" in df_last.columns:
        sessions = df_last["Session"].astype(str)
        times = mdates.date2num(df_last.index.to_pydatetime())
        current, start_idx = None, None
        for i, s in enumerate(sessions):
            if s != current:
                if current in ("London", "NY") and start_idx is not None:
                    ax.axvspan(times[start_idx], times[i - 1],
                               facecolor="yellow" if current=="London" else "lightblue",
                               alpha=0.2, zorder=0, label=current)
                current, start_idx = s, i
        if current in ("London", "NY") and start_idx is not None:
            ax.axvspan(times[start_idx], times[-1],
                       facecolor="yellow" if current=="London" else "lightblue",
                       alpha=0.2, zorder=0, label=current)

    # Trade markers
    if "TradeAction" in df_last.columns:
        buys     = df_last[df_last["TradeAction"]=="BUY"]
        sells    = df_last[df_last["TradeAction"]=="SELL"]
        exits_tp = df_last[df_last["TradeAction"]=="EXIT-TP"]
        exits_sl = df_last[df_last["TradeAction"]=="EXIT-SL"]

        ax.scatter(mdates.date2num(buys.index),  buys[price_col], marker="^", c="green", s=60, label="BUY", zorder=3)
        ax.scatter(mdates.date2num(sells.index), sells[price_col], marker="v", c="red",   s=60, label="SELL", zorder=3)
        ax.scatter(mdates.date2num(exits_tp.index), exits_tp[price_col], marker="o", c="blue", s=40, label="EXIT-TP", zorder=3)
        ax.scatter(mdates.date2num(exits_sl.index), exits_sl[price_col], marker="x", c="orange", s=60, label="EXIT-SL", zorder=3)

    # Add sentiment text box
    if sentiment:
        sentiment_str = "\n".join([f"{k}: {v}" for k, v in sentiment.items()])
        ax.text(1.01, 0.5, sentiment_str,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment="center",
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"))

    # Formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d\n%H:%M"))
    ax.set_title("USDMXN Signals (last 300 bars)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"Chart exported to {fname}")
    return fname
