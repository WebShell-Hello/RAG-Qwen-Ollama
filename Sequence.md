sequenceDiagram
    autonumber
    participant U as User (Browser)
    participant S as Streamlit App (Python)
    participant E as Embedding (Ollama: nomic-embed-text)
    participant I as FAISS Index
    participant P as Prompt Builder
    participant L as LLM (Ollama: DeepSeek/Qwen)

    U->>S: Enter question
    S->>E: embed(question)
    E-->>S: query_vector
    S->>I: search(query_vector, k)
    I-->>S: chunk_ids + scores
    S->>P: build(system + question + context)
    P-->>S: prompt
    S->>L: chat(prompt)
    L-->>S: answer
    S-->>U: show answer + retrieved chunks
