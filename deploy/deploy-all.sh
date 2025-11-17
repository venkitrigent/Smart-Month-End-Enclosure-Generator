#!/bin/bash

# Deploy all agents to Google Cloud Run
# Make sure you're authenticated: gcloud auth login

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${GCP_REGION:-"us-central1"}

echo "Deploying to project: $PROJECT_ID in region: $REGION"

# Deploy Orchestrator
echo "Deploying Orchestrator..."
gcloud run deploy orchestrator \
  --source ../agents/orchestrator \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID"

# Deploy Classifier
echo "Deploying Classifier..."
gcloud run deploy classifier \
  --source ../agents/classifier \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

# Deploy Extractor
echo "Deploying Extractor..."
gcloud run deploy extractor \
  --source ../agents/extractor \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

# Deploy Checklist
echo "Deploying Checklist..."
gcloud run deploy checklist \
  --source ../agents/checklist \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

# Deploy Analytics
echo "Deploying Analytics..."
gcloud run deploy analytics \
  --source ../agents/analytics \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated

# Deploy Chatbot
echo "Deploying Chatbot..."
gcloud run deploy chatbot \
  --source ../agents/chatbot \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID"

# Deploy Frontend
echo "Deploying Frontend..."
gcloud run deploy frontend \
  --source ../frontend \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8501

echo "Deployment complete!"
echo "Get service URLs with: gcloud run services list"
