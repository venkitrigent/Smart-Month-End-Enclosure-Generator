# 🚀 Quick Start - Deploy in 10 Minutes

## What Changed (Important!)

### ✅ Embeddings: Now Using Vertex AI (Google Cloud Native)
- **Before:** Downloaded sentence-transformers model (slow, large)
- **Now:** Uses Vertex AI `textembedding-gecko@003` (fast, no download!)
- **Benefit:** Works instantly in Cloud Run, no model download needed

### ✅ LLM: Using Your Azure ChatOpenAI
- **Before:** Would need to host a model
- **Now:** Uses your existing Azure OpenAI deployment
- **Benefit:** No model hosting, just API calls to your Azure endpoint

---

## Prerequisites

1. ✅ Google Cloud Project with billing enabled
2. ✅ Azure OpenAI deployment (your existing one)
3. ✅ Code pushed to GitHub
4. ✅ `gcloud` CLI installed

---

## Step 1: Generate API Key (30 seconds)

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Save this output!** Example: `xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s`

---

## Step 2: Configure Environment (2 minutes)

Create `adk-orchestrator/.env`:

```bash
# Environment
ENVIRONMENT=production

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GCP_REGION=us-central1

# BigQuery & Firestore
BIGQUERY_DATASET=financial_close
FIRESTORE_COLLECTION=sessions

# Vertex AI Embedding (Google Cloud - no download needed!)
VERTEX_EMBEDDING_MODEL=textembedding-gecko@003

# Azure OpenAI (Your existing deployment)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# API Key (from Step 1)
API_KEYS=xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s

# Firebase (OPTIONAL - skip for now)
# FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json
```

**Replace:**
- `your-gcp-project-id` → Your actual GCP project ID
- `your-resource.openai.azure.com` → Your Azure OpenAI endpoint
- `your-azure-openai-key` → Your Azure OpenAI API key
- `xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s` → Your generated API key

---

## Step 3: Deploy Backend to Cloud Run (5 minutes)

```bash
# Navigate to backend
cd adk-orchestrator

# Deploy (this builds and deploys automatically)
gcloud run deploy month-end-close-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project) \
  --set-env-vars GCP_REGION=us-central1 \
  --set-env-vars BIGQUERY_DATASET=financial_close \
  --set-env-vars VERTEX_EMBEDDING_MODEL=textembedding-gecko@003 \
  --set-env-vars AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
  --set-env-vars AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4 \
  --set-env-vars AZURE_OPENAI_API_VERSION=2024-02-15-preview \
  --set-env-vars API_KEYS=your-api-key \
  --set-env-vars AZURE_OPENAI_API_KEY=your-azure-key
```

**Get your backend URL:**
```bash
gcloud run services describe month-end-close-api \
  --region us-central1 \
  --format 'value(status.url)'
```

**Save this URL!** Example: `https://month-end-close-api-xxxxx-uc.a.run.app`

---

## Step 4: Test Backend (1 minute)

```bash
# Test health endpoint
curl https://month-end-close-api-xxxxx-uc.a.run.app/health

# Should return:
# {"status":"healthy","service":"month-end-close-agent"}
```

---

## Step 5: Deploy Frontend to Streamlit Community Cloud (2 minutes)

### 5.1: Go to Streamlit Cloud
1. Visit: https://streamlit.io/cloud
2. Sign in with GitHub
3. Click **"New app"**

### 5.2: Configure App
- **Repository:** `your-username/smart-month-end-close`
- **Branch:** `main`
- **Main file path:** `frontend/app.py`

### 5.3: Add Secrets
Click **"Advanced settings"** → **"Secrets"** and paste:

```toml
BACKEND_URL = "https://month-end-close-api-xxxxx-uc.a.run.app"
API_KEY = "xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s"
```

**Replace with your actual values!**

### 5.4: Deploy
Click **"Deploy!"**

Wait 2-3 minutes. Your app will be live at: `https://your-app.streamlit.app`

---

## 🎉 Done! Test Your App

1. Open your Streamlit URL
2. Sign in (any email/password works in dev mode)
3. Upload a CSV file
4. Check the chat feature
5. Generate a report

---

## Key Points

### ✅ What's Using Google Cloud (Free/Cheap):
- **Embeddings:** Vertex AI `textembedding-gecko@003` (native, fast)
- **Storage:** BigQuery, Firestore, Cloud Storage
- **Hosting:** Cloud Run (backend)

### ✅ What's Using Azure:
- **LLM:** Your Azure ChatOpenAI deployment (gpt-4)
- **Only for:** Chat responses, document classification, analysis

### ✅ What's FREE:
- **Frontend:** Streamlit Community Cloud (completely free!)
- **Backend:** Cloud Run free tier (first 2M requests/month)
- **Vertex AI Embeddings:** Free tier available

---

## Troubleshooting

### "Permission denied" errors
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable firestore.googleapis.com
```

### "Cannot connect to backend"
- Check `BACKEND_URL` in Streamlit secrets
- Make sure it starts with `https://`
- No trailing slash

### "Azure OpenAI error"
- Verify `AZURE_OPENAI_ENDPOINT` is correct
- Check `AZURE_OPENAI_API_KEY` is valid
- Confirm `AZURE_OPENAI_DEPLOYMENT_NAME` exists

---

## Cost Estimate

### Monthly costs for moderate usage (1000 requests/month):

- **Cloud Run (Backend):** $0-5
- **Vertex AI Embeddings:** $0-2
- **BigQuery:** $0-1
- **Firestore:** $0-1
- **Streamlit Frontend:** $0 (FREE)
- **Azure OpenAI:** Based on your Azure pricing

**Total Google Cloud:** ~$5-10/month
**Streamlit:** FREE

---

## Next Steps

1. ✅ Test all features
2. ✅ Upload sample CSV files
3. ✅ Try the chat feature
4. ✅ Generate reports
5. ✅ Share URL with users

---

## Support Files

- **Full Guide:** `COMPLETE_DEPLOYMENT_GUIDE.md`
- **Firebase Setup:** `FIREBASE_SETUP_GUIDE.md` (optional)
- **Streamlit Guide:** `STREAMLIT_COMMUNITY_CLOUD_GUIDE.md`
- **Authentication:** `AUTHENTICATION_GUIDE.md`

---

## Summary

**You're using:**
1. ✅ **Vertex AI embeddings** (Google Cloud native - fast!)
2. ✅ **Azure ChatOpenAI** (your existing LLM)
3. ✅ **Cloud Run** (backend hosting)
4. ✅ **Streamlit Community Cloud** (frontend - FREE!)

**No model downloads, no local hosting, everything cloud-native!** 🚀
