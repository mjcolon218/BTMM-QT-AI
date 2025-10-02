from chart_export import export_trade_chart
import pandas as pd

# Load your last backtest signals with trades (adjust path if needed)
df = pd.read_csv("outputs/signals/usdmxn_signals_with_trades.csv", parse_dates=["Datetime"]).set_index("Datetime")

# Generate chart PNG
chart_path = export_trade_chart(df, "outputs/alerts/test_chart.png", price_col="Close", ema_col="EMA_50",sentiment=None)
print("✅ Chart saved at:", chart_path)
print(df.tail(5)[["Close","Signal","TradeAction","Session"]])
