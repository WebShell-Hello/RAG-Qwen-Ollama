```mermaid
graph TB
    subgraph Client
        Browser[User Browser]
    end

    subgraph Host[MacBook / Local Host]
        subgraph App[Streamlit App (Python)]
            UI2[UI + Logging]
            RAG[Custom RAG Pipeline<br/>PDF→Chunk→Embed→FAISS→Prompt]
        end
        
        subgraph Ollama[Ollama Runtime]
            EMBM[nomic-embed-text]
            LLM1[DeepSeek-R1-14B]
            LLM2[Qwen2.5-14B]
        end
        
        Vec[FAISS Index + Metadata]
        Files[PDF Files]
    end

    Browser --> UI2
    UI2 --> RAG
    RAG -->|embed query| EMBM
    RAG -->|generate answer| LLM1
    RAG -->|alternative| LLM2
    RAG -->|search| Vec
    RAG -->|read| Files
    
    %% 样式定义
    classDef client fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef host fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef app fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef ollama fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    
    class Client client
    class Host host
    class App app
    class Ollama ollama
```
