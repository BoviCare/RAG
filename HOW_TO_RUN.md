# 🐄 BoviCare - How to Run the Code

This document provides comprehensive instructions for running all the code components in the BoviCare repository. Each component serves a specific purpose in the bovine disease information system.

## 📋 Table of Contents

1. [RAG-bovicare - Main RAG System](#rag-bovicare---main-rag-system)
2. [FastAPI - General RAG Chat](#fastapi---general-rag-chat)
3. [fastapi-vibe-coding - Advanced RAG with Hybrid Search](#fastapi-vibe-coding---advanced-rag-with-hybrid-search)
4. [RAG-funds - Financial Documents RAG](#rag-funds---financial-documents-rag)
5. [diagnose_disease - AI Disease Diagnosis](#diagnose_disease---ai-disease-diagnosis)
6. [HealthBenchmark - Model Evaluation](#healthbenchmark---model-evaluation)
7. [AWS Infrastructure Deployment](#aws-infrastructure-deployment)

---

## 🎯 RAG-bovicare - Main RAG System

**Purpose**: The primary RAG system for bovine disease information with hybrid search and AI reranking.

### Prerequisites
- Python 3.8+
- OpenAI API key
- Milvus (local or cloud)

### Setup & Run

```bash
# Navigate to the directory
cd RAG-bovicare

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_api_key_here"
# Optional: For cloud Milvus
export MILVUS_URI="your_milvus_uri"
export MILVUS_API_TOKEN="your_milvus_token"

# Ingest data into vector database (first time only)
python ingest_data.py

# Start the application
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Access Points
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Key Features
- Hybrid search (dense + sparse vectors)
- AI-powered reranking
- Specialized in bovine diseases
- Beautiful chatbot interface

---

## 🚀 FastAPI - General RAG Chat

**Purpose**: A general-purpose RAG chat application with Milvus integration.

### Setup & Run

```bash
cd FastAPI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_api_key_here"
export MILVUS_URI="your_milvus_uri"
export MILVUS_API_TOKEN="your_milvus_token"

# Start the application
uvicorn main:app --reload
```

### Access Points
- **Chat Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Features
- Real-time chat with RAG
- Document addition via API
- Modern web interface

---

## 🔍 fastapi-vibe-coding - Advanced RAG with Hybrid Search

**Purpose**: Advanced RAG system with hybrid search capabilities and beautiful UI.

### Setup & Run

```bash
cd fastapi-vibe-coding

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_api_key_here"
export MILVUS_URI="https://in03-4efcec782ae2f4c.serverless.gcp-us-west1.cloud.zilliz.com"
export MILVUS_TOKEN="dca9ee30dd6accca68a63953d96a07cf3295cb68d1df55d93823135499762886d4ea0c5cb68b7307f72afce73a991ebc16447360"

# Start the application
python main.py
```

### Access Points
- **Chat Interface**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health

### Features
- Advanced hybrid search
- Beautiful responsive UI
- Real-time status monitoring
- Document management

---

## 💰 RAG-funds - Financial Documents RAG

**Purpose**: RAG system specialized for financial documents with advanced hybrid search.

### Setup & Run

```bash
cd RAG-funds

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export OPENAI_API_KEY="your_openai_api_key_here"
export MILVUS_URI="http://localhost:19530"  # or your Milvus URI
export MILVUS_API_TOKEN="your_milvus_token"  # optional for local

# Start Milvus (if using local)
docker-compose up -d

# Process documents (first time)
python process_documents.py

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Access Points
- **Chat Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Features
- Financial document processing
- Hybrid search with BM25
- AI-powered reranking
- Duplicate prevention

---

## 🩺 diagnose_disease - AI Disease Diagnosis

**Purpose**: AI-powered disease diagnosis system for veterinary use.

### Setup & Run

```bash
cd diagnose_disease

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export LLM_PROVIDER="openai"  # or other provider
export LLM_PROVIDER_MODEL="gpt-4"  # or other model
export LLM_PROVIDER_KEY="your_api_key_here"

# Run the diagnosis system
python src/runner.py
```

### Features
- AI-powered disease diagnosis
- Structured output with Pydantic models
- Veterinary expertise integration
- Symptom analysis

---

## 📊 HealthBenchmark - Model Evaluation

**Purpose**: Evaluation framework for language models on various benchmarks.

### Setup & Run

```bash
cd HealthBenchmark

# Install dependencies (varies by eval)
pip install -r requirements.txt

# For specific evals, install additional dependencies:
# HumanEval
git clone https://github.com/openai/human-eval
pip install -e human-eval

# OpenAI API
pip install openai

# Anthropic API
pip install anthropic

# Set up API keys
export OPENAI_API_KEY="your_openai_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"

# List available models
python -m simple-evals.simple_evals --list-models

# Run evaluations
python -m simple-evals.simple_evals --model <model_name> --examples <num_examples>
```

### Available Benchmarks
- MMLU (Massive Multitask Language Understanding)
- MATH (Mathematical Problem Solving)
- GPQA (Graduate-Level Q&A)
- DROP (Reading Comprehension)
- MGSM (Multilingual Math)
- HumanEval (Code Generation)
- SimpleQA (Factuality)
- BrowseComp (Browsing Agents)
- HealthBench (Health-related tasks)

---

## ☁️ AWS Infrastructure Deployment

**Purpose**: Deploy the BoviCare RAG system to AWS using Terraform.

### Prerequisites
- AWS CLI configured
- Terraform installed
- Docker installed
- GitHub repository with Actions enabled

### Setup & Deploy

```bash
cd aws_infrastructure

# Copy and customize variables
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply infrastructure
terraform apply
```

### Manual AWS Setup Required

1. **Create IAM User**:
   - Create user `terraform-user` with programmatic access
   - Attach policies: EC2, ECR, S3, RDS, VPC, IAM, Secrets Manager

2. **Create S3 Bucket**:
   - Bucket name: `bovicare-terraform-state`
   - Enable versioning

3. **Create DynamoDB Table**:
   - Table name: `terraform-state-locks`
   - Primary key: `LockID` (String)

4. **Create EC2 Key Pair**:
   - Name: `bovicare-key-pair`
   - Download and save the .pem file

5. **Create Secrets Manager Secret**:
   - Secret name: `bovicare/prod/app/secrets`
   - Secret value:
     ```json
     {
       "openai_api_key": "your_openai_api_key",
       "milvus_uri": "your_milvus_uri",
       "milvus_api_token": "your_milvus_token"
     }
     ```

6. **GitHub Actions Secrets**:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

### Deployment Process
1. Push to main branch triggers automatic deployment
2. Terraform creates all AWS resources
3. EC2 instance runs user data script
4. Docker containers are pulled and started
5. Application becomes available at EC2 public IP

---

## 🔧 Common Troubleshooting

### Environment Variables
Make sure all required environment variables are set:
- `OPENAI_API_KEY`: Required for all AI components
- `MILVUS_URI`: Required for vector database
- `MILVUS_API_TOKEN`: Required for cloud Milvus

### Port Conflicts
If you get port conflicts, change the port:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Dependencies Issues
If you encounter dependency conflicts:
```bash
# Create fresh virtual environment
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Milvus Connection Issues
- For local Milvus: Make sure Milvus is running on the correct port
- For cloud Milvus: Verify URI and token are correct
- Check network connectivity

### AWS Deployment Issues
- Verify AWS credentials are configured
- Check IAM permissions
- Ensure all manual setup steps are completed
- Check Terraform state for errors

---

## 📚 Additional Resources

### API Documentation
- RAG-bovicare: http://localhost:8000/docs
- FastAPI: http://localhost:8000/docs
- fastapi-vibe-coding: http://localhost:8000/docs
- RAG-funds: http://localhost:8000/docs

### Health Checks
- RAG-bovicare: http://localhost:8000/health
- FastAPI: http://localhost:8000/health
- fastapi-vibe-coding: http://localhost:8000/api/health
- RAG-funds: http://localhost:8000/health

### Logs
- Application logs: Check console output
- AWS logs: CloudWatch Logs
- Docker logs: `docker logs <container_name>`

---

## 🎯 Quick Start Summary

For a quick start with the main BoviCare system:

```bash
# 1. Set up the main RAG system
cd RAG-bovicare
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your_key_here"
python ingest_data.py
python main.py

# 2. Access at http://localhost:8000
```

This will give you the full BoviCare RAG system running locally with all features enabled.

---

## 📞 Support

For issues or questions:
1. Check the logs for error messages
2. Verify all environment variables are set
3. Ensure all dependencies are installed
4. Check network connectivity for external services
5. Review the specific README files in each component directory

Each component has its own detailed README with specific instructions and troubleshooting tips.
