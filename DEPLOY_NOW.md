# 🚀 Deploy Now - Complete Step-by-Step Guide

## Overview: What You Need to Do

```
1. Setup Databases (5 min) ← Run script once
2. Configure .env (2 min)   ← Add your credentials
3. Deploy Backend (5 min)   ← Cloud Run deployment
4. Deploy Frontend (2 min)  ← Streamlit Community Cloud
```

**Total Time: ~15 minutes**

---

## Prerequisites Check

```bash
# Check if gcloud is installed
gcloud --version

# Check if you're logged in
gcloud auth list

# Check your project
gcloud config get-value project

# If no project set:
gcloud config set project YOUR_PROJECT_ID
```

---

## Step 1: Setup Databases (ONE TIME ONLY)

### What This Does:
- Creates BigQuery dataset with 3 tables
- Enables Firestore database
- Creates Cloud Storage bucket
- Sets up IAM permissions
- Enables required APIs

### Run This:

```bash
# Make script executable
chmod +x setup-databases.sh

# Run setup
./setup-databases.sh
```

**This will:**
1. Ask for confirmation
2. Enable Google Cloud APIs
3. Create BigQuery dataset `financial_close`
4. Create 3 tables: `documents`, `structured_data`, `embeddings`
5. Enable Firestore
6. Create Cloud Storage bucket
7. Set IAM permissions

**Output:** You'll see green checkmarks ✅ for each step.

**Time:** ~5 minutes

---

## Step 2: Configure Environment

### 2.1: Generate API Key

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Copy the output!** Example: `xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s`

### 2.2: Create .env File

```bash
cd adk-orchestrator
cp .env.example .env
nano .env  # or use your favorite editor
```

### 2.3: Fill in Your Values

```bash
# Environment
ENVIRONMENT=production

# Google Cloud (from Step 1)
GOOGLE_CLOUD_PROJECT=your-project-id-here
GOOGLE_CLOUD_LOCATION=us-central1
GCP_REGION=us-central1

# BigQuery & Firestore (created by setup script)
BIGQUERY_DATASET=financial_close
FIRESTORE_COLLECTION=sessions

# Vertex AI Embedding (Google Cloud - no setup needed!)
VERTEX_EMBEDDING_MODEL=textembedding-gecko@003

# Azure OpenAI (YOUR CREDENTIALS)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-azure-openai-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# API Key (from Step 2.1)
API_KEYS=xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s

# Firebase (OPTIONAL - skip for now)
# FIREBASE_SERVICE_ACCOUNT=./firebase-service-account.json
```

**Save the file!**

---

## Step 3: Deploy Backend to Cloud Run

### Option A: Simple Deploy (Recommended)

```bash
cd adk-orchestrator

# Load environment variables
source .env

# Deploy
gcloud run deploy month-end-close-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT \
  --set-env-vars GCP_REGION=$GCP_REGION \
  --set-env-vars BIGQUERY_DATASET=$BIGQUERY_DATASET \
  --set-env-vars FIRESTORE_COLLECTION=$FIRESTORE_COLLECTION \
  --set-env-vars VERTEX_EMBEDDING_MODEL=$VERTEX_EMBEDDING_MODEL \
  --set-env-vars AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
  --set-env-vars AZURE_OPENAI_DEPLOYMENT_NAME=$AZURE_OPENAI_DEPLOYMENT_NAME \
  --set-env-vars AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION \
  --set-env-vars API_KEYS=$API_KEYS \
  --set-env-vars AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
```

### Option B: Use Deployment Script

```bash
chmod +x deploy/deploy-backend-cloudrun.sh
./deploy/deploy-backend-cloudrun.sh
```

### What Happens:
1. Cloud Build creates a Docker container
2. Uploads to Container Registry
3. Deploys to Cloud Run
4. Returns a URL

**Time:** ~5 minutes (first time), ~2 minutes (subsequent)

### Get Your Backend URL:

```bash
gcloud run services describe month-end-close-api \
  --region us-central1 \
  --format 'value(status.url)'
```

**Save this URL!** Example: `https://month-end-close-api-xxxxx-uc.a.run.app`

---

## Step 4: Test Backend

```bash
# Replace with your actual URL
BACKEND_URL="https://month-end-close-api-xxxxx-uc.a.run.app"

# Test health endpoint
curl $BACKEND_URL/health

# Should return:
# {"status":"healthy","service":"month-end-close-agent","features":{...}}
```

**If you see this, backend is working!** ✅

---

## Step 5: Deploy Frontend to Streamlit Community Cloud

### 5.1: Go to Streamlit Cloud

1. Visit: https://streamlit.io/cloud
2. Click **"Sign in"** or **"Sign up"**
3. Choose **"Continue with GitHub"**
4. Authorize Streamlit to access your repositories

### 5.2: Create New App

1. Click **"New app"** button
2. Fill in the form:
   - **Repository:** `your-username/smart-month-end-close`
   - **Branch:** `main`
   - **Main file path:** `frontend/app.py`

### 5.3: Add Secrets

1. Click **"Advanced settings"**
2. In the **"Secrets"** text box, paste:

```toml
BACKEND_URL = "https://month-end-close-api-xxxxx-uc.a.run.app"
API_KEY = "xK9mP2nQ4rT6vY8zA1bC3dE5fG7hJ9kL0mN2oP4qR6s"
```

**Replace with YOUR actual values:**
- `BACKEND_URL` = Your Cloud Run URL from Step 3
- `API_KEY` = Your API key from Step 2.1

### 5.4: Deploy

1. Click **"Deploy!"**
2. Wait 2-3 minutes
3. Your app will be live!

**Your app URL:** `https://your-app-name.streamlit.app`

---

## Step 6: Test Complete System

### 6.1: Open Your Streamlit App

Go to: `https://your-app-name.streamlit.app`

### 6.2: Sign In

- **Email:** any-email@example.com
- **Password:** any-password (min 6 chars)

*(Development mode allows any credentials)*

### 6.3: Test Upload

1. Click **"📤 Upload"** in sidebar
2. Upload a CSV file (bank statement, invoice, etc.)
3. Click **"📊 Process & Generate Report"**
4. Wait for processing
5. Check results!

### 6.4: Test Chat

1. Click **"💬 Chat"** in sidebar
2. Ask: "What documents have I uploaded?"
3. Check if it responds with your data

### 6.5: Test Report

1. Click **"📊 Report"** in sidebar
2. Click **"📄 Generate Report"**
3. View the month-end close report

---

## Troubleshooting

### Issue: "Permission denied" during database setup

**Solution:**
```bash
# Make sure you're project owner or editor
gcloud projects get-iam-policy $(gcloud config get-value project)

# Or run with your user account
gcloud auth application-default login
```

### Issue: "Dataset already exists"

**Solution:** This is fine! The script will skip creation and use existing dataset.

### Issue: Backend deployment fails

**Solution:**
```bash
# Check logs
gcloud run services logs read month-end-close-api --region us-central1

# Common fixes:
# 1. Check .env file has all values
# 2. Verify Azure OpenAI credentials
# 3. Make sure APIs are enabled
```

### Issue: Frontend can't connect to backend

**Solution:**
1. Check `BACKEND_URL` in Streamlit secrets
2. Make sure URL starts with `https://`
3. No trailing slash
4. Test backend directly: `curl YOUR_BACKEND_URL/health`

### Issue: "Azure OpenAI error"

**Solution:**
1. Verify endpoint URL is correct
2. Check API key is valid
3. Confirm deployment name exists in Azure
4. Test Azure OpenAI directly from Azure portal

---

## What Databases Were Created?

### BigQuery Dataset: `financial_close`

**Tables:**

1. **documents** - Metadata about uploaded files
   - Columns: document_id, filename, doc_type, user_id, upload_time, row_count, columns

2. **structured_data** - Parsed CSV data
   - Columns: row_id, document_id, doc_type, row_index, data, created_at

3. **embeddings** - Vector embeddings for RAG
   - Columns: embedding_id, document_id, row_index, chunk_text, embedding, metadata, created_at

### Firestore Database: `(default)`

**Collections:**
- `sessions` - Chat history and user sessions
- `checklists` - Month-end close checklist status

### Cloud Storage Bucket: `your-project-id-month-end-close`

**Purpose:** Store uploaded files (optional, currently using BigQuery)

---

## Cost Breakdown

### One-Time Setup: FREE
- Database creation: FREE
- API enablement: FREE

### Monthly Running Costs (Estimated):

**Google Cloud:**
- Cloud Run: $0-5 (free tier covers most usage)
- BigQuery: $0-2 (first 1TB queries free)
- Firestore: $0-1 (free tier covers most usage)
- Vertex AI Embeddings: $0-3
- **Total GCP: ~$5-10/month**

**Streamlit Community Cloud:**
- Frontend hosting: **FREE** ✅

**Azure OpenAI:**
- Based on your Azure pricing plan
- Typically $0.002-0.03 per 1K tokens

**Total: ~$5-15/month for moderate usage**

---

## Summary Checklist

- [ ] Databases set up (ran `setup-databases.sh`)
- [ ] `.env` file configured with credentials
- [ ] Backend deployed to Cloud Run
- [ ] Backend URL obtained and saved
- [ ] Frontend deployed to Streamlit Community Cloud
- [ ] Secrets added to Streamlit (BACKEND_URL, API_KEY)
- [ ] Tested sign in
- [ ] Tested file upload
- [ ] Tested chat feature
- [ ] Tested report generation

---

## 🎉 You're Done!

Your Smart Month-End Close system is now live and ready to use!

**Share your Streamlit URL with users and start automating financial close processes!**

---

## Quick Reference

```bash
# View backend logs
gcloud run services logs read month-end-close-api --region us-central1

# Update backend
cd adk-orchestrator
gcloud run deploy month-end-close-api --source .

# View BigQuery data
bq query --use_legacy_sql=false 'SELECT * FROM financial_close.documents LIMIT 10'

# Check Firestore
gcloud firestore databases list
```

---

## Support

- **Backend Issues:** Check Cloud Run logs
- **Frontend Issues:** Check Streamlit app logs (in dashboard)
- **Database Issues:** Check BigQuery/Firestore in GCP Console
- **Azure Issues:** Check Azure OpenAI deployment status

**Need help?** Check the detailed guides:
- `COMPLETE_DEPLOYMENT_GUIDE.md`
- `FIREBASE_SETUP_GUIDE.md`
- `STREAMLIT_COMMUNITY_CLOUD_GUIDE.md`
