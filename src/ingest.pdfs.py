import fitz, json
from pathlib import Path
from uuid import uuid4

def chunk_text(text, size=800, overlap=150):
    step = size - overlap
    for i in range(0, len(text), step):
        yield text[i:i+size]

if __name__ == "__main__":
    raw = Path("data/raw_pdfs"); out = Path("kb/chunks")
    out.mkdir(parents=True, exist_ok=True)
    for pdf in raw.glob("*.pdf"):
        doc = fitz.open(pdf)
        with open(out / f"{pdf.stem}.jsonl", "w", encoding="utf-8") as w:
            for p in doc:
                txt = p.get_text("text")
                for ch in chunk_text(txt):
                    w.write(json.dumps({"source": pdf.name, "text": ch.strip()}) + "\n")
        doc.close()
        print(f"Processed {pdf.name}")
    print("Done")