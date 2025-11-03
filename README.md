# 🐄 BoviCare - Bovine Disease Information System

A sophisticated Retrieval-Augmented Generation (RAG) system for bovine disease information with hybrid search, AI-powered reranking, and multiple specialized components.

## 🚀 Quick Start

### Prerequisites
- Python >3.11
- OpenAI API key

### 1. Setup Environment
```bash
# Clone the repository
git clone <repository-url>
cd BoviCare

# Set OpenAI API key
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 2. Run Main System
```bash
cd RAG-bovicare
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Only run this if you don't have Milvus configured yet (first time setup)
python ingest_data.py

python main.py
```

### 3. Access Application
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🔑 Environment Variables

### Required
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### Optional
```bash
# For cloud Milvus (optional - uses local if not provided)
export MILVUS_URI="your_MILVUS_URI_here"
export MILVUS_TOKEN="your_MILVUS_API_TOKEN_here"

---

## 📋 Components

| Component | Purpose | Run Command |
|-----------|---------|-------------|
| **RAG-bovicare** | Main bovine disease RAG | `cd RAG-bovicare && python main.py` (run `python ingest_data.py` first if no Milvus data) |
| **FastAPI** | General RAG chat | `cd FastAPI && uvicorn main:app --reload` |
| **VetBench** | Veterinary model evaluation | `cd RAG-bovicare && python test_vetbench_healthbench_style.py` |

## 🎯 Features

- **Hybrid Search**: Combines dense vector embeddings with BM25 sparse search
- **AI Reranking**: Uses OpenAI to intelligently rerank search results
- **Specialized Knowledge**: Focused on bovine diseases and veterinary medicine
