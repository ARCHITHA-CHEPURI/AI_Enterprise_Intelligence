# AI Enterprise Intelligence: Hybrid KG + RAG Chatbot

An advanced, enterprise-grade chatbot platform that leverages a **Hybrid Retrieval-Augmented Generation (RAG)** architecture. It combines the structured logical relations of a **Knowledge Graph (Neo4j)** with the semantic power of **Vector Search (FAISS)** to provide highly accurate, context-aware answers from diverse enterprise data sources.

---

## 🚀 Key Features

- **Hybrid Retrieval**: Seamlessly integrates Knowledge Graph triples and Vector embeddings for superior context retrieval.
- **Multi-Format Ingestion**: Supports PDF, DOCX, PPTX, CSV, Excel, and JSON data.
- **Enterprise UI**: A premium, responsive web interface with real-time streaming, theme toggling, and interactive suggestions.
- **Advanced Metrics**: Evaluates every response for **Accuracy**, **Precision**, and **Confidence** based on retrieved chunks.
- **Scalable Pipeline**: Handles large-scale data imports (2GB+ datasets) using Git LFS and automated processing scripts.

---

## 🏗️ Architecture

The system operates on a three-tier RAG pipeline:

1.  **Data Ingestion**: Extracts text and relationships from raw documents.
2.  **Hybrid Indexing**: 
    - **Vector DB**: Chunks text and generates embeddings using `all-MiniLM-L6-v2`.
    - **Knowledge Graph**: Extracts entities and relationships into Neo4j.
3.  **Generation**: Orchestrates state-of-the-art LLMs (via Ollama) to synthesize answers from both indices.

---

## 🛠️ Project Structure

```text
chatbot_proj/
├── Data/               # Raw and processed datasets (PDF, Excel, JSON, etc.)
├── scripts/            # Core logic for RAG and data processing
│   ├── hybrid_rag.py   # Main hybrid retrieval & generation script
│   ├── data_ingestion.py # Robust multi-format document loader
│   └── ...             # Utility and evaluation scripts
├── static/             # Frontend assets (HTML, Modern CSS, JS)
├── app.py              # FastAPI server for the web interface
└── requirements.txt    # Project dependencies
```

---

## 🏁 Getting Started

### Prerequisites

- **Python 3.10+**
- **Neo4j**: Database for Knowledge Graph storage.
- **Ollama**: Local LLM runner (defaults to `llama3.2:1b`).
- **Dependencies**: Install via pip.

### Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Databases**:
   Ensure Neo4j is running on `localhost:7687` and Ollama is active on `localhost:11434`.

3. **Ingest Data**:
   ```bash
   python scripts/data_ingestion.py
   python scripts/embedding_generation_pipeline.py
   python scripts/push_to_neo4j.py
   ```

### Launch the UI

```bash
python app.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 📊 Evaluation & Metrics

The system automatically calculates and displays performance metrics for every query:
- **Accuracy**: Relevance of the answer to the provided context.
- **Precision**: Directness and fact-usage of the LLM.
- **Confidence**: Statistical score of the retrieval success.

---

## 📄 License
*Check repository LICENSE for details.*