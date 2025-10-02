# src/backtest.py
import pandas as pd, json
from spec_schema import StrategySpec
from signal_engine import signalize
from backtest_utils import equity_with_trades, kpis  # assume you have this

# ---- Load Bars ----
def load_bars(path):
    df = pd.read_csv(path, parse_dates=["Datetime"]).set_index("Datetime").sort_index()
    return df[["Open","High","Low","Close","Volume"]]

# ---- Add Session Column ----
def add_sessions(df):
    """
    Adds a 'Session' column (Asia, London, NY, Other) based on hour.
    Adjust bins to match your broker's timezone (assuming UTC here).
    """
    hrs = df.index.hour
    df["Session"] = pd.cut(
        hrs,
        bins=[-1, 6, 11, 16, 23],   # 0–6 Asia, 7–11 London, 12–16 NY, 17–23 Other
        labels=["Asia", "London", "NY", "Other"]
    ).astype(str)
    return df

# ---- Main Run ----
if __name__ == "__main__":
    # Load spec (update path to AI spec or starter spec)
    spec = StrategySpec.model_validate_json(
        open("outputs/specs/usdmxn_quarters_bmm.json").read()
    )

    # Load bars and add sessions
    df = load_bars("data/market/USDMXN_M15.csv")
    df = add_sessions(df)

    # Generate signals
    df = signalize(df, spec)

    # Run backtest with trades annotated
    df = equity_with_trades(df, atr_col="ATR_14", tp_rr=2.0, sl_atr_mult=1.5)

    # Save outputs
    df.to_csv("outputs/signals/usdmxn_signals_with_trades.csv")
    eq = df["Equity"]
    eq.to_csv("outputs/backtests/usdmxn_equity.csv")

    # KPIs
    print(json.dumps(kpis(eq), indent=2))
    print(kpis(df['Equity']))
    # Optional: show signal counts
    print("Signal counts:", df["Signal"].value_counts())
    print("Trade counts:", df["TradeAction"].value_counts())
    # Optional: plot df buy and sells
    from plot_trade import plot_price_with_trades
    import matplotlib.pyplot as plt
    plot_price_with_trades(df)
    plt.show()
    #print(df.head(150))