# Complete Deployment Guide - Smart Month-End Close

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT ARCHITECTURE                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │   Streamlit      │         │   Backend API    │         │
│  │  Community Cloud │────────▶│   Cloud Run      │         │
│  │  (Frontend)      │  HTTPS  │   (FastAPI)      │         │
│  └──────────────────┘         └──────────────────┘         │
│                                        │                     │
│                                        ▼                     │
│                          ┌──────────────────────┐           │
│                          │  Google Cloud        │           │
│                          │  - BigQuery          │           │
│                          │  - Firestore         │           │
│                          │  - Cloud Storage     │           │
│                          │  - Vertex AI         │           │
│                          └──────────────────────┘           │
│                                        │                     │
│                                        ▼                     │
│                          ┌──────────────────────┐           │
│                          │  Azure OpenAI        │           │
│                          │  (Your LLM)          │           │
│                          └──────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. GitHub Repository Setup

### Step 1.1: Push Your Code to GitHub

```bash
# Initialize git (if not already done)
cd /path/to/your/project
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Smart Month-End Close system"

# Create GitHub repo (do this on GitHub.com first)
# Then connect and push
git remote add origin https://github.com/YOUR_USERNAME/smart-month-end-close.git
git branch -M main
git push -u origin main
```

### Step 1.2: Repository Structure

Your GitHub repo should have:
```
smart-month-end-close/
├── adk-orchestrator/          # Backend (Cloud Run)
│   ├── server.py
│   ├── month_end_agent/
│   ├── services/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                  # Streamlit (Community Cloud)
│   ├── app.py
│   ├── requirements.txt
│   └── .env.example
├── deploy/
│   └── deploy-backend.sh
└── README.md
```

**IMPORTANT**: Do NOT push `.env` files with secrets! Only push `.env.example`

---

## 2. API Key Authentication Setup

### Step 2.1: Generate API Keys

```bash
# Generate a secure API key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Example output: xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s
```

### Step 2.2: Configure Backend (.env)

In `adk-orchestrator/.env`:
```bash
# Environment
ENVIRONMENT=production

# API Keys (comma-separated for multiple keys)
API_KEYS=xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s,another-key-for-admin

# Google Cloud
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
BIGQUERY_DATASET=month_end_close
FIRESTORE_COLLECTION=month_end_sessions

# Azure OpenAI (see section 3)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Firebase (optional - for user auth)
FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json
```

### Step 2.3: Store Secrets in Cloud Run

```bash
# Set secrets as environment variables in Cloud Run
gcloud run services update month-end-close-api \
  --update-env-vars API_KEYS=xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s \
  --update-env-vars AZURE_OPENAI_API_KEY=your-azure-key \
  --region us-central1
```

### Step 2.4: Configure Frontend (.env)

In `frontend/.env` (for Streamlit Community Cloud):
```bash
# Backend API URL (your Cloud Run URL)
BACKEND_URL=https://month-end-close-api-xxxxx-uc.a.run.app

# API Key for authentication
API_KEY=xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s
```

---

## 3. Azure OpenAI Integration (Instead of Local Model)

### Step 3.1: Update Backend to Use Azure OpenAI

Create `adk-orchestrator/services/azure_llm_service.py`:

```python
"""
Azure OpenAI Service for LLM calls
"""
import os
from openai import AzureOpenAI

class AzureLLMService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    def generate_response(self, prompt: str, system_message: str = None) -> str:
        """Generate response using Azure OpenAI"""
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    def generate_embeddings(self, text: str) -> list:
        """Generate embeddings using Azure OpenAI"""
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"  # Use your Azure embedding model
        )
        return response.data[0].embedding

# Global instance
azure_llm = AzureLLMService()
```

### Step 3.2: Update Agent to Use Azure OpenAI

Modify `adk-orchestrator/month_end_agent/agent.py`:

```python
from services.azure_llm_service import azure_llm

# In your agent tools, replace local model calls with Azure OpenAI
def analyze_financial_data(data: str) -> dict:
    """Analyze financial data using Azure OpenAI"""
    
    system_message = """You are a financial analyst expert. 
    Analyze the provided financial data and provide insights."""
    
    prompt = f"""Analyze this financial data:
    {data}
    
    Provide:
    1. Key insights
    2. Anomalies or concerns
    3. Recommendations
    """
    
    response = azure_llm.generate_response(prompt, system_message)
    
    return {
        "analysis": response,
        "model": "azure-openai"
    }
```

### Step 3.3: Update Requirements

Add to `adk-orchestrator/requirements.txt`:
```
openai>=1.0.0
```

---

## 4. Deploy Backend to Cloud Run

### Step 4.1: Create Dockerfile

`adk-orchestrator/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Step 4.2: Create requirements.txt for Backend

`adk-orchestrator/requirements.txt`:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
google-cloud-bigquery==3.13.0
google-cloud-firestore==2.13.1
google-cloud-storage==2.10.0
google-cloud-aiplatform==1.38.0
firebase-admin==6.2.0
sentence-transformers==2.2.2
pandas==2.1.4
python-dotenv==1.0.0
openai>=1.0.0
pydantic==2.5.0
```

### Step 4.3: Deploy to Cloud Run

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Build and deploy
cd adk-orchestrator

gcloud run deploy month-end-close-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GCP_PROJECT_ID=YOUR_PROJECT_ID \
  --set-env-vars BIGQUERY_DATASET=month_end_close \
  --set-env-vars AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
  --set-env-vars AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4 \
  --set-secrets API_KEYS=api-keys:latest \
  --set-secrets AZURE_OPENAI_API_KEY=azure-openai-key:latest

# Get the URL
gcloud run services describe month-end-close-api \
  --region us-central1 \
  --format 'value(status.url)'
```

**Output**: `https://month-end-close-api-xxxxx-uc.a.run.app`

### Step 4.4: Test Backend

```bash
# Test health endpoint
curl https://month-end-close-api-xxxxx-uc.a.run.app/health

# Test with API key
curl -X POST https://month-end-close-api-xxxxx-uc.a.run.app/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@test.csv"
```

---

## 5. Deploy Frontend to Streamlit Community Cloud

### Step 5.1: Prepare Streamlit App

Rename `frontend/app.py` to `frontend/streamlit_app.py` (Streamlit Community Cloud convention):

```bash
cd frontend
mv app.py streamlit_app.py
```

### Step 5.2: Update Frontend to Use API Key

Modify `frontend/streamlit_app.py`:

```python
import os
import streamlit as st
import requests

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "")

# Helper function with API key
def make_request(method, endpoint, **kwargs):
    """Make authenticated API request"""
    headers = kwargs.pop('headers', {})
    
    # Add API key authentication
    if API_KEY:
        headers['X-API-Key'] = API_KEY
    
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, **kwargs)
        elif method == "POST":
            response = requests.post(url, headers=headers, **kwargs)
        return response
    except Exception as e:
        st.error(f"Request failed: {str(e)}")
        return None
```

### Step 5.3: Create Streamlit Requirements

`frontend/requirements.txt`:
```
streamlit==1.29.0
requests==2.31.0
pandas==2.1.4
plotly==5.18.0
```

### Step 5.4: Push to GitHub

```bash
git add frontend/
git commit -m "Prepare frontend for Streamlit Community Cloud"
git push origin main
```

### Step 5.5: Deploy to Streamlit Community Cloud

1. Go to https://streamlit.io/cloud
2. Sign up/Login with GitHub
3. Click "New app"
4. Select:
   - Repository: `your-username/smart-month-end-close`
   - Branch: `main`
   - Main file path: `frontend/streamlit_app.py`
5. Click "Advanced settings"
6. Add secrets:
   ```toml
   BACKEND_URL = "https://month-end-close-api-xxxxx-uc.a.run.app"
   API_KEY = "xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s"
   ```
7. Click "Deploy"

**Your app will be live at**: `https://your-app-name.streamlit.app`

---

## 6. Alternative: Deploy Streamlit on Cloud Run

If you prefer Cloud Run for everything:

### Step 6.1: Create Dockerfile for Streamlit

`frontend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 6.2: Deploy Streamlit to Cloud Run

```bash
cd frontend

gcloud run deploy month-end-close-frontend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars BACKEND_URL=https://month-end-close-api-xxxxx-uc.a.run.app \
  --set-secrets API_KEY=api-keys:latest
```

---

## 7. Complete Deployment Checklist

### ✅ Backend (Cloud Run)
- [ ] Code pushed to GitHub
- [ ] Azure OpenAI credentials configured
- [ ] API keys generated and stored in Secret Manager
- [ ] Dockerfile created
- [ ] Deployed to Cloud Run
- [ ] Health endpoint tested
- [ ] Upload endpoint tested with API key

### ✅ Frontend (Streamlit Community Cloud)
- [ ] `streamlit_app.py` created
- [ ] Requirements.txt updated
- [ ] Code pushed to GitHub
- [ ] Deployed to Streamlit Community Cloud
- [ ] Secrets configured (BACKEND_URL, API_KEY)
- [ ] App tested and working

### ✅ Integration
- [ ] Frontend can connect to backend
- [ ] API key authentication working
- [ ] File upload working
- [ ] Chat feature working
- [ ] Report generation working

---

## 8. Quick Start Commands

### Deploy Everything:

```bash
# 1. Deploy Backend
cd adk-orchestrator
gcloud run deploy month-end-close-api --source . --region us-central1

# 2. Get Backend URL
BACKEND_URL=$(gcloud run services describe month-end-close-api \
  --region us-central1 --format 'value(status.url)')

echo "Backend URL: $BACKEND_URL"

# 3. Push to GitHub
git add .
git commit -m "Deploy smart month-end close"
git push origin main

# 4. Deploy Frontend to Streamlit Community Cloud
# Go to https://streamlit.io/cloud and follow steps above
```

---

## 9. Environment Variables Summary

### Backend (.env)
```bash
ENVIRONMENT=production
API_KEYS=your-secure-api-key
GCP_PROJECT_ID=your-project-id
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
```

### Frontend (Streamlit Secrets)
```toml
BACKEND_URL = "https://your-backend-url.run.app"
API_KEY = "your-secure-api-key"
```

---

## 10. Troubleshooting

### Backend Issues:
```bash
# View logs
gcloud run services logs read month-end-close-api --region us-central1

# Test locally
cd adk-orchestrator
uvicorn server:app --reload
```

### Frontend Issues:
- Check Streamlit Community Cloud logs in the app dashboard
- Verify BACKEND_URL is correct
- Verify API_KEY matches backend

---

## 🎉 You're Done!

Your app is now live:
- **Backend API**: `https://month-end-close-api-xxxxx.run.app`
- **Frontend**: `https://your-app.streamlit.app`

Share the Streamlit URL with users!
