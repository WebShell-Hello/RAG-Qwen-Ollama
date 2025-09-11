import streamlit as st
import os
import json
import requests
import numpy as np
import faiss
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen/qwen-3b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
FAISS_PATH = os.getenv("FAISS_PATH", "wm_manual.faiss")
META_PATH = os.getenv("META_PATH", "wm_manual_meta.json")
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "query_log.jsonl")

def load_index(faiss_path, meta_path):
    if not os.path.exists(faiss_path) or not os.path.exists(meta_path):
        st.error(f"FAISS index or metadata not found. Run ingest.py first. Expected: {faiss_path}, {meta_path}")
        st.stop()
    index = faiss.read_index(faiss_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return index, meta

def get_embedding(text):
    url = f"{OLLAMA_URL}/api/embeddings"
    payload = {"model": EMBED_MODEL, "prompt": text}
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "embedding" in data:
        emb = np.array(data["embedding"], dtype=np.float32)
    else:
        emb = np.array(data["data"][0]["embedding"], dtype=np.float32)
    return emb

def search_similar(index, query_emb, k=4):
    q = np.array([query_emb], dtype=np.float32)
    faiss.normalize_L2(q)
    D, I = index.search(q, k)
    return I[0].tolist(), D[0].tolist()

def call_ollama_chat(system_prompt, user_prompt):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "qwen:1.8b",  # make sure this model is pulled with `ollama pull qwen:7b`
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()

    # Ollama returns {"message": {"role": "...", "content": "..."}}
    data = resp.json()
    return data["message"]["content"]


def log_query(entry):
    # append jsonl
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

st.set_page_config(page_title="Washing Machine Service Chatbot", layout="wide")
st.title("Washing Machine Service Chatbot (RAG + Qwen / Ollama)")

tabs = st.tabs(["Chat", "Admin (Logs & Retrieved Contexts)"])

# load index once
index, meta = load_index(FAISS_PATH, META_PATH)

with tabs[0]:
    col1, col2 = st.columns([3,1])
    with col1:
        user_input = st.text_area("Describe symptoms / ask question:", height=180)
        concise = st.checkbox("Short answers only", value=True)
        top_k = st.number_input("Top-k retrieved chunks", min_value=1, max_value=8, value=int(os.getenv("TOP_K", 4)))
        if st.button("Ask"):
            if not user_input.strip():
                st.warning("Please enter a symptom or question.")
            else:
                with st.spinner("Searching manual and calling model..."):
                    qemb = get_embedding(user_input)
                    ids, scores = search_similar(index, qemb, k=top_k)
                    contexts = []
                    for idx in ids:
                        contexts.append(meta[idx]["text"])
                    system_prompt = (
                        "You are a service-assistant specialized in washing machine repair. "
                        "Use ONLY the provided context from the official service manual to determine root causes and give concise, actionable troubleshooting steps. "
                        "If the manual does not contain an answer, say 'Not in manual' and suggest safe next diagnostic steps."
                    )
                    retrieved_text = "\n\n---\n\n".join(contexts)
                    user_prompt = (
                        f"Symptom / question:\n{user_input}\n\n"
                        f"Context (from Service Manual):\n{retrieved_text}\n\n"
                        + ("Provide a concise diagnosis (1-2 short bullets) and next troubleshooting steps (2 short bullets)." if concise else "Provide a diagnosis and step-by-step troubleshooting instructions, citing context where relevant.")
                    )
                    answer = call_ollama_chat(system_prompt, user_prompt)
                    now = datetime.utcnow().isoformat() + "Z"
                    log_entry = {
                        "timestamp": now,
                        "question": user_input,
                        "retrieved_ids": ids,
                        "retrieved_scores": scores,
                        "answer": answer
                    }
                    log_query(log_entry)
                    st.success("Done")
                    st.markdown("**Assistant:**")
                    st.write(answer)
                    with st.expander("Show retrieved manual snippets (for verification)"):
                        for i, cid in enumerate(ids):
                            st.markdown(f"**Chunk #{cid}** — score: {scores[i]:.4f}")
                            st.write(meta[cid]["text"][:2000])
    with col2:
        st.markdown("### Quick controls")
        st.info("Make sure you ran ingest.py and have wm_manual.faiss + wm_manual_meta.json in the app folder.")
        st.markdown("**Logs**: saved to `logs/query_log.jsonl`.")

with tabs[1]:
    st.header("Admin — Recent queries")
    if not os.path.exists(LOG_PATH):
        st.info("No logs yet. Use Chat tab to generate activity.")
    else:
        # show most recent logs
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f if l.strip()]
        lines = list(reversed(lines))
        n = st.number_input("Show last N entries", min_value=1, max_value=200, value=10)
        for entry in lines[:n]:
            st.markdown(f"**Time:** {entry['timestamp']}")
            st.markdown(f"**Question:** {entry['question']}")
            st.markdown(f"**Answer:** {entry['answer']}")
            st.markdown(f"**Retrieved chunk IDs:** {entry['retrieved_ids']}")
            if st.checkbox(f"Show contexts for query at {entry['timestamp']}", key=entry['timestamp']):
                for cid in entry['retrieved_ids']:
                    st.markdown(f"- **Chunk {cid}**:\n\n{meta[cid]['text'][:4000]}")
            st.write('---')
