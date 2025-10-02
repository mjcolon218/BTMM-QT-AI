# src/spec_from_docs.py
import os, json, faiss, numpy as np
from dotenv import load_dotenv
import re
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from spec_schema import StrategySpec

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def retrieve(query, k=10):
    metas = [json.loads(l) for l in open("kb/vectors/meta.jsonl", encoding="utf-8")]
    model = SentenceTransformer("all-MiniLM-L6-v2")
    q = model.encode([query], normalize_embeddings=True).astype("float32")
    index = faiss.read_index("kb/vectors/trading.faiss")
    _, I = index.search(q, k)
    return "\n\n".join([metas[i]["text"] for i in I[0]])

if __name__ == "__main__":
    ctx = retrieve("Quarters Theory and Beat the Market Maker: entries, exits, stop hunts, session timing, quarter levels")
    system = system = """
You are an expert quant.
Return ONLY valid JSON that matches this schema (no text, no markdown, no explanations):

{
  "name": "string",
  "timeframe": "M15",
  "instruments": ["USDMXN"],
  "indicators": [
    {"name": "RSI", "params": {"period": 14}, "alias": "RSI_14"},
    {"name": "ATR", "params": {"period": 14}, "alias": "ATR_14"},
    {"name": "EMA", "params": {"period": 21}, "alias": "EMA_50"},
    {"name": "QuarterGrid", "params": {"size_pips": 25, "pip_scale": 0.0001}, "alias": "QG"}
  ],
  "entries": [
    {"side": "LONG", "condition": "(RSI_14 < 35) and (Close > EMA_21) and (QG == 'Q1')", "session": "London"},
    {"side": "SHORT", "condition": "(RSI_14 > 65) and (Close < EMA_21) and (QG == 'Q4')", "session": "NY"}
  ],
  "exits": [
    {"type": "TP_SL", "params": {"tp_rr": 2.0, "sl_atr_mult": 1.5}}
  ],
  "risk": {"fixed_fraction": 0.01, "max_positions": 1}
}
"""

    user = f"Using this context, produce one USD/MXN M15 StrategySpec with realistic thresholds:\n{ctx}"
    msg = client.chat.completions.create(model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":user}]
    ).choices[0].message.content

import json, re
from pydantic import ValidationError

def clean_and_validate(msg: str):
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", msg.strip(), flags=re.MULTILINE)
    try:
        return StrategySpec.model_validate_json(clean)
    except ValidationError as e:
        print("Validation failed, trying auto-fix...")
        # Try json.loads to see if it's a dict
        try:
            parsed = json.loads(clean)
            # If indicators dict → convert to list
            if isinstance(parsed.get("indicators"), dict):
                parsed["indicators"] = [
                    {"name": k, "params": v, "alias": f"{k}_{list(v.values())[0]}"}
                    for k,v in parsed["indicators"].items()
                ]
            return StrategySpec.model_validate(parsed)
        except Exception as inner:
            print("Auto-fix also failed")
            raise e

# Remove ```json or ``` wrappers if present
 
spec = clean_and_validate(msg)  # raises if invalid
open("outputs/specs/usdmxn_from_ai.json", "w").write(spec.model_dump_json(indent=2))
print("Wrote outputs/specs/usdmxn_from_ai.json")
print(spec)