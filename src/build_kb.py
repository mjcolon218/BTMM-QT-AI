import json, faiss, numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

if __name__ == "__main__":
    texts, meta = [], []
    for jf in Path("kb/chunks").glob("*.jsonl"):
        for line in open(jf, encoding="utf-8"):
            row = json.loads(line); texts.append(row["text"]); meta.append(row)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embs = model.encode(texts, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embs.shape[1]); index.add(np.array(embs, dtype="float32"))
    faiss.write_index(index, "kb/vectors/trading.faiss")
    with open("kb/vectors/meta.jsonl","w",encoding="utf-8") as f:
        for m in meta: f.write(json.dumps(m)+"\n")
    print(f"Indexed {len(texts)} chunks")
    print("Done")