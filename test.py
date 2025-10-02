import faiss, json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("kb/vectors/trading.faiss")
metas = [json.loads(l) for l in open("kb/vectors/meta.jsonl")]

query = "combine the steve mauro method with quarters theory for the usdmxn and give me strategy ideas"
vec = model.encode([query], normalize_embeddings=True).astype("float32")
D, I = index.search(vec, 3)
for i in I[0]:
    print(metas[i]["text"])
