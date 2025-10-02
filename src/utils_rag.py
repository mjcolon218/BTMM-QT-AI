# src/utils_rag.py
import faiss, json
import numpy as np
from sentence_transformers import SentenceTransformer

def retrieve_from_vector_db(query, k=5):
    """Retrieve top-k chunks from FAISS for a query"""
    metas = [json.loads(l) for l in open("kb/vectors/meta.jsonl", encoding="utf-8")]
    model = SentenceTransformer("all-MiniLM-L6-v2")
    q = model.encode([query], normalize_embeddings=True).astype("float32")
    index = faiss.read_index("kb/vectors/trading.faiss")
    _, I = index.search(q, k)
    return [metas[i]["text"] for i in I[0]]
