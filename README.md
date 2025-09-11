# Washing Machine Service Chatbot (Streamlit + Ollama + RAG)

This repository provides a ready-to-run Streamlit chatbot that uses a locally-hosted Ollama Qwen model
enhanced with a Washing Machine Service Manual via RAG (FAISS). It includes an admin panel that logs
queries and shows which manual chunks were retrieved for each reply.

## What's included
- `ingest.py` — Ingests a PDF manual, chunks text, generates embeddings via Ollama, and builds a FAISS index.
- `streamlit_app.py` — Streamlit UI for engineers + admin page showing logs and retrieved contexts.
- `requirements.txt`
- `Dockerfile`
- `.env.example`
- `.gitignore`
- `make_zip.sh` (helper)

## Quick steps (summary)
1. Install and run Ollama on your host. Pull a Qwen chat model and an embedding model into Ollama.
   Example:
   ```bash
   ollama pull qwen/qwen-3b
   ollama pull nomic-embed-text
   ollama serve
   ```
2. Create a `.env` file from `.env.example` and set values.
3. Install Python deps:
   ```bash
   pip install -r requirements.txt
   ```
4. Ingest the PDF (once):
   ```bash
   python ingest.py --pdf /path/to/WashingMachineServiceManual.pdf --out wm_manual
   ```
   This writes `wm_manual.faiss` and `wm_manual_meta.json`.
5. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```
   Open http://localhost:8501

## Docker (optional)
Build:
```bash
docker build -t wm-chatbot:latest .
docker run -p 8501:8501 --add-host=host.docker.internal:host-gateway wm-chatbot:latest
```

## Notes
- The app depends on Ollama's REST API at `OLLAMA_URL` (default http://localhost:11434).
- The admin page logs each query in `logs/query_log.jsonl`.
- The repository does NOT contain the service manual PDF (you will supply it).
