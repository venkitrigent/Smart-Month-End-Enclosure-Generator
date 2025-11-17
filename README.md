# Smart Month-End Enclosure Generator

AI-powered financial close automation platform using Google Cloud, ADK & Vertex AI.

## 🏗️ Architecture

This project uses **Google Agent Development Kit (ADK)** with a multi-agent architecture:

- **ADK Orchestrator Agent**: Master agent coordinating document processing workflow
- **Chatbot Agent**: Q&A assistant with context awareness
- **Cloud Storage**: Document uploads
- **BigQuery**: Structured financial data
- **Firestore**: Session memory and chat history
- **Vertex AI**: Gemini for LLM capabilities

## 🚀 Quick Start

### Option 1: Deploy ADK Agent to Cloud Run (Recommended)

```bash
# 1. Set your GCP project
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1

# 2. Deploy ADK agent
cd deploy
chmod +x deploy-adk-agent.sh
./deploy-adk-agent.sh

# 3. Access the web UI at the provided URL
```

### Option 2: Local Development

```bash
# 1. Setup ADK agent
cd adk-orchestrator
cp .env.example .env
# Edit .env with your project details

# 2. Install dependencies with uv
pip install uv
uv sync

# 3. Run locally
uv run uvicorn server:app --host 0.0.0.0 --port 8080

# 4. Access at http://localhost:8080/web
```

## 📊 Testing

### Test the deployed agent
```bash
# Health check
curl https://your-service-url/health

# Access web UI
open https://your-service-url/web
```

### Run elasticity test
```bash
cd adk-orchestrator
uv run locust -f elasticity_test.py \
  -H https://your-service-url \
  --headless -t 60s -u 20 -r 5
```

## 🎯 Key Features

- **CSV-only processing** for rapid demo
- **Multi-agent orchestration** with ADK
- **Automated checklist** tracking
- **Financial analytics** with anomaly detection
- **AI-powered chatbot** with session memory
- **Cloud Run autoscaling** for production workloads

## 📁 Project Structure

```
smart-month-end-close/
├── adk-orchestrator/          # ADK agent (main service)
│   ├── month_end_agent/       # Agent implementation
│   │   ├── agent.py          # Multi-agent definitions
│   │   └── __init__.py
│   ├── server.py             # FastAPI server
│   ├── Dockerfile            # Container config
│   ├── pyproject.toml        # Dependencies
│   └── elasticity_test.py    # Load testing
├── deploy/
│   └── deploy-adk-agent.sh   # Deployment script
├── sample_data/              # Test CSV files
└── frontend/                 # Optional Streamlit UI
```
