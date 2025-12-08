# 🐄 BoviCare - Bovine Disease Information System

A sophisticated Retrieval-Augmented Generation (RAG) system for bovine disease information with hybrid search, AI-powered reranking, and multiple specialized components.

## 🚀 Deployment

This repository is configured with **GitHub Actions** for automated deployment to AWS (EC2).

### Deployment Flow
1.  Any push to the `main` branch triggers the deployment workflow.
2.  The Docker image is built and pushed to Amazon ECR.
3.  The service on the EC2 instance is updated via AWS Systems Manager (SSM).

### Required Secrets
Ensure these repository secrets are set:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`

## 🚀 Quick Start (Local)

### Prerequisites
- Python >3.11
- OpenAI API key
- Docker and Docker Compose (for Docker setup)

### Important: Project Structure

The BoviCare project consists of 3 separate GitHub repositories:
- `RAG` - This repository (RAG service)
- `bovicare-api` - Backend API (Flask) - **Contains `docker-compose.yml`**
- `bovicare-web` - Frontend (React)

**The `docker-compose.yml` file is located in the `bovicare-api` repository**, not in this repository. See the `bovicare-api` README for complete setup instructions.

### 1. Setup Environment

**Important:** For Docker setup, the `.env` file should be in the `bovicare-api` directory (where `docker-compose.yml` is located).

For local development (without Docker), create a `.env` file in the `RAG` directory:

```bash
# Create .env file
touch .env
```

Then add the following variables to your `.env` file:

```env
# Required: OpenAI API Key for AI-powered responses
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Milvus Vector Database Configuration
# If not provided, the system will use local Milvus instance
MILVUS_URI=your_milvus_uri_here
MILVUS_API_TOKEN=your_milvus_api_token_here

# Optional: Email Configuration (for notifications/password reset)
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_email_password_here
```

**Note:** Make sure to add `.env` to your `.gitignore` file to avoid committing sensitive credentials.

### 2. Running with Docker Compose (Recommended)

The easiest way to run the complete application is using Docker Compose. The `docker-compose.yml` file is located in the `bovicare-api` repository.

**Setup Instructions:**
1. Clone all 3 repositories into the same parent directory
2. Create a `.env` file in the `bovicare-api` directory
3. Run `docker-compose up -d` from the `bovicare-api` directory

See the `bovicare-api` README for detailed instructions.

### 3. Run RAG Service Locally (Without Docker)

```bash
cd RAG
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Only run this if you don't have Milvus configured yet (first time setup)
python ingest_data.py

python main.py
```

### 4. Access Application
- **RAG Service**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🔑 Environment Variables

**For Docker Setup:** The `.env` file should be in the `bovicare-api` directory (where `docker-compose.yml` is located).

**For Local Development:** Create a `.env` file in the `RAG` directory with the following variables:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI-powered responses and reranking | `sk-...` |

### Optional Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MILVUS_URI` | Milvus vector database URI (for cloud Milvus) | `https://your-instance.milvus.io` |
| `MILVUS_API_TOKEN` | Milvus API token for authentication | `your_token_here` |
| `EMAIL_USER` | Email address for sending notifications | `your_email@example.com` |
| `EMAIL_PASSWORD` | Email password or app-specific password | `your_password_here` |

**Note:** 
- If `MILVUS_URI` and `MILVUS_API_TOKEN` are not provided, the system will use a local Milvus instance.
- Email variables are only needed if email functionality is required (e.g., password reset, notifications).

### Example `.env` File

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here

# Optional - Milvus (cloud)
MILVUS_URI=https://your-instance.milvus.io
MILVUS_API_TOKEN=your_milvus_token_here

# Optional - Email
EMAIL_USER=your_email@example.com
EMAIL_PASSWORD=your_email_password_here
```

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
