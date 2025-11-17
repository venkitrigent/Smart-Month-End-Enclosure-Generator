#!/bin/bash

# Deploy Frontend to Google Cloud Run (Alternative to Streamlit Community Cloud)
# Use this if you want to host Streamlit on Cloud Run instead of Community Cloud

set -e

echo "🚀 Deploying Streamlit Frontend to Cloud Run"
echo "=============================================="

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="month-end-close-frontend"
BACKEND_URL="${BACKEND_URL:-}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check backend URL
if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}❌ BACKEND_URL not set!${NC}"
    echo "Please set BACKEND_URL environment variable:"
    echo "  export BACKEND_URL=https://your-backend-url.run.app"
    exit 1
fi

# Check API key
if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ API_KEY not set!${NC}"
    echo "Please set API_KEY environment variable:"
    echo "  export API_KEY=your-api-key"
    exit 1
fi

# Set project
echo -e "${YELLOW}📋 Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars BACKEND_URL=$BACKEND_URL \
  --set-env-vars API_KEY=$API_KEY

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=============================================="
echo -e "${GREEN}Frontend URL: $SERVICE_URL${NC}"
echo ""
echo "Your app is now live! Share this URL with users."
echo ""
