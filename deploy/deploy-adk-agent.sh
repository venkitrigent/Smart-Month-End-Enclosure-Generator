#!/bin/bash

# Deploy ADK Agent to Cloud Run
# Based on Google Cloud Run ADK deployment best practices

set -e

PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME="month-end-close-agent"

echo "🚀 Deploying ADK Agent to Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com

# Deploy to Cloud Run
echo "🔨 Building and deploying..."
gcloud run deploy $SERVICE_NAME \
  --source ../adk-orchestrator \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 5 \
  --min-instances 0 \
  --concurrency 50 \
  --timeout 300 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-env-vars GOOGLE_CLOUD_LOCATION=$REGION \
  --set-env-vars GEMINI_MODEL=gemini-2.0-flash-exp \
  --labels app=month-end-close,component=adk-agent

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format='value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Web UI: $SERVICE_URL/web"
echo "📖 API Docs: $SERVICE_URL/docs"
echo "💚 Health: $SERVICE_URL/health"
echo ""
echo "🧪 Test with:"
echo "curl $SERVICE_URL/health"
echo ""
echo "🔥 Run elasticity test:"
echo "cd ../adk-orchestrator"
echo "uv run locust -f elasticity_test.py -H $SERVICE_URL --headless -t 60s -u 20 -r 5"
