import os, requests, pandas as pd
from dotenv import load_dotenv
load_dotenv()
API = os.getenv("POLYGON_API_KEY")

def fetch(start, end, multiplier=15, timespan="minute"):
    url = f"https://api.polygon.io/v2/aggs/ticker/C:USDMXN/range/{multiplier}/{timespan}/{start}/{end}"
    r = requests.get(url, params={"adjusted":"true","sort":"asc","limit":50000,"apiKey":API})
    r.raise_for_status()
    js = r.json()
    if "results" not in js: raise RuntimeError(js)
    df = pd.DataFrame(js["results"])
    df["Datetime"] = pd.to_datetime(df["t"], unit="ms")
    df = df.rename(columns={"o":"Open","h":"High","l":"Low","c":"Close","v":"Volume"})
    return df[["Datetime","Open","High","Low","Close","Volume"]]

if __name__ == "__main__":
    df = fetch("2025-09-01","2025-10-01")
    df.to_csv("data/market/USDMXN_M15.csv", index=False)
    print(df.head())
