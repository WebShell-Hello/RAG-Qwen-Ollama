flowchart LR
    %% Offline preprocessing
    subgraph OFFLINE[Offline: KB Build]
      PDF[PDF Manuals] -->|PyPDF2| TXT[Extracted Text]
      TXT -->|Chunk 400 / Overlap 80| CH[Chunks]
      CH -->|Ollama: nomic-embed-text| EMB[Embeddings]
      EMB -->|add| FAISS[(FAISS Index)]
      CH --> META[Chunk Metadata (JSON)]
    end

    %% Online inference
    subgraph ONLINE[Online: Query & Answer]
      UI[Streamlit UI] -->|user question| QEMB[Query Embedding\n(Ollama: nomic-embed-text)]
      QEMB -->|search top-k| FAISS
      FAISS --> CTX[Top-k Context Chunks]
      CTX --> PROMPT[Prompt Builder\n(System + Question + Context)]
      PROMPT --> LLM[LLM via Ollama\n(DeepSeek-R1-14B / Qwen2.5-14B)]
      LLM --> ANS[Answer]
      ANS --> UI
      CTX --> UI
    end
