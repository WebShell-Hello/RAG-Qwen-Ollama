import os
import json
import requests
import numpy as np
from tqdm import tqdm
from PyPDF2 import PdfReader
import faiss
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")

def read_pdf(path):
    reader = PdfReader(path)
    pages = []
    for p in range(len(reader.pages)):
        try:
            pages.append(reader.pages[p].extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages)

def chunk_text(text, chunk_size=400, overlap=80):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks

def get_embedding(text):
    url = f"{OLLAMA_URL}/api/embeddings"
    payload = {"model": EMBED_MODEL, "prompt": text}
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "embedding" in data:
        return np.array(data["embedding"], dtype=np.float32)
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        return np.array(data["data"][0]["embedding"], dtype=np.float32)
    raise ValueError("Unexpected embedding response: " + str(data))

def main(pdf_path, out_prefix="wm_manual"):
    text = read_pdf(pdf_path)
    chunks = chunk_text(text, chunk_size=400, overlap=80)
    embeddings = []
    metadata = []
    for i, chunk in enumerate(tqdm(chunks, desc="Embedding chunks")):
        emb = get_embedding(chunk)
        embeddings.append(emb)
        metadata.append({"id": i, "text": chunk})
    embeddings = np.vstack(embeddings).astype(np.float32)
    faiss.normalize_L2(embeddings)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, f"{out_prefix}.faiss")
    with open(f"{out_prefix}_meta.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print("Saved:", f"{out_prefix}.faiss", f"{out_prefix}_meta.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path to service manual PDF")
    parser.add_argument("--out", default="wm_manual", help="Output prefix")
    args = parser.parse_args()
    main(args.pdf, args.out)
