# src/sentiment.py
def market_sentiment(df):
    """
    Summarizes market sentiment based on BTMM concepts:
    - Peak formations (High/Low)
    - Levels (1, 2, 3)
    - Quarters Grid
    """

    last = df.iloc[-1]
    sentiment = {}

    # --- Peak Formation (PFH/PFL) ---
    if last["Close"] == df["High"].rolling(50).max().iloc[-1]:
        sentiment["PF"] = "Peak Formation High (PFH)"
    elif last["Close"] == df["Low"].rolling(50).min().iloc[-1]:
        sentiment["PF"] = "Peak Formation Low (PFL)"
    else:
        sentiment["PF"] = "No new PF"

    # --- Levels (simple approximation using rolling) ---
    swings = df["Close"].rolling(50).mean().diff().tail(3)
    if swings.iloc[-1] > 0:
        sentiment["Level"] = "Level 2 (Accumulation)"
    else:
        sentiment["Level"] = "Level 3 (Distribution)"

    # --- Quarters Grid ---
    qg = last.get("QG", "Unknown")
    sentiment["Quarter"] = f"Currently in {qg}"

    # --- Bias ---
    if "PFL" in sentiment["PF"]:
        bias = "Bullish bias → expect upward push"
    elif "PFH" in sentiment["PF"]:
        bias = "Bearish bias → expect downward push"
    else:
        bias = "Neutral bias"
    sentiment["Bias"] = bias

    return sentiment
