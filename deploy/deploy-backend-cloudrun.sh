#!/bin/bash

# Deploy Backend to Google Cloud Run
# This script deploys the FastAPI backend with Azure OpenAI integration

set -e

echo "🚀 Deploying Smart Month-End Close Backend to Cloud Run"
echo "=========================================================="

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="month-end-close-api"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Set project
echo -e "${YELLOW}📋 Setting GCP project to: $PROJECT_ID${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com

# Navigate to backend directory
cd "$(dirname "$0")/../adk-orchestrator"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please create .env from .env.example and configure your settings."
    exit 1
fi

# Load environment variables
source .env

# Validate Azure OpenAI configuration
if [ -z "$AZURE_OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ AZURE_OPENAI_API_KEY not set in .env${NC}"
    exit 1
fi

if [ -z "$API_KEYS" ]; then
    echo -e "${YELLOW}⚠️  API_KEYS not set. Generating one...${NC}"
    API_KEYS=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo -e "${GREEN}✅ Generated API Key: $API_KEYS${NC}"
    echo "Add this to your .env file!"
fi

# Deploy to Cloud Run
echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-env-vars GCP_REGION=$REGION \
  --set-env-vars BIGQUERY_DATASET=$BIGQUERY_DATASET \
  --set-env-vars FIRESTORE_COLLECTION=$FIRESTORE_COLLECTION \
  --set-env-vars AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
  --set-env-vars AZURE_OPENAI_DEPLOYMENT_NAME=$AZURE_OPENAI_DEPLOYMENT_NAME \
  --set-env-vars AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION \
  --set-env-vars API_KEYS=$API_KEYS \
  --set-env-vars AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --format 'value(status.url)')

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================================="
echo -e "${GREEN}Backend URL: $SERVICE_URL${NC}"
echo ""
echo "Test your deployment:"
echo "  curl $SERVICE_URL/health"
echo ""
echo "API Key for authentication:"
echo "  $API_KEYS"
echo ""
echo "Next steps:"
echo "  1. Test the backend: curl $SERVICE_URL/health"
echo "  2. Update frontend BACKEND_URL to: $SERVICE_URL"
echo "  3. Deploy frontend to Streamlit Community Cloud"
echo ""
