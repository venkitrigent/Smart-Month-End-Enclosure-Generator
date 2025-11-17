#!/bin/bash

# Complete Deployment Script for Smart Month-End Close System
# This script guides you through the entire deployment process

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Smart Month-End Close - Complete Deployment Script      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check Prerequisites
echo -e "${YELLOW}Step 1: Checking Prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ git not found${NC}"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# Step 2: Configuration
echo -e "${YELLOW}Step 2: Configuration${NC}"
echo "Please provide the following information:"
echo ""

read -p "GCP Project ID: " GCP_PROJECT_ID
read -p "GCP Region [us-central1]: " GCP_REGION
GCP_REGION=${GCP_REGION:-us-central1}

read -p "Azure OpenAI Endpoint: " AZURE_OPENAI_ENDPOINT
read -p "Azure OpenAI API Key: " AZURE_OPENAI_API_KEY
read -p "Azure OpenAI Deployment Name [gpt-4]: " AZURE_OPENAI_DEPLOYMENT_NAME
AZURE_OPENAI_DEPLOYMENT_NAME=${AZURE_OPENAI_DEPLOYMENT_NAME:-gpt-4}

echo ""
echo -e "${YELLOW}Generating API Key for authentication...${NC}"
API_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo -e "${GREEN}Generated API Key: $API_KEY${NC}"
echo -e "${YELLOW}⚠️  Save this API key! You'll need it for the frontend.${NC}"
echo ""

# Step 3: Update .env file
echo -e "${YELLOW}Step 3: Creating .env file...${NC}"

cat > adk-orchestrator/.env << EOF
# Environment
ENVIRONMENT=production

# Google Cloud
GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID
GOOGLE_CLOUD_LOCATION=$GCP_REGION
GCP_REGION=$GCP_REGION

# BigQuery
BIGQUERY_DATASET=financial_close

# Firestore
FIRESTORE_COLLECTION=sessions

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=$AZURE_OPENAI_DEPLOYMENT_NAME
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# API Keys
API_KEYS=$API_KEY
EOF

echo -e "${GREEN}✅ .env file created${NC}"
echo ""

# Step 4: Deploy Backend
echo -e "${YELLOW}Step 4: Deploying Backend to Cloud Run...${NC}"
read -p "Deploy backend now? (y/n): " deploy_backend

if [ "$deploy_backend" = "y" ]; then
    export GCP_PROJECT_ID
    export GCP_REGION
    ./deploy/deploy-backend-cloudrun.sh
    
    # Get backend URL
    BACKEND_URL=$(gcloud run services describe month-end-close-api \
      --region $GCP_REGION \
      --format 'value(status.url)')
    
    echo ""
    echo -e "${GREEN}✅ Backend deployed successfully!${NC}"
    echo -e "${GREEN}Backend URL: $BACKEND_URL${NC}"
else
    echo -e "${YELLOW}⏭️  Skipping backend deployment${NC}"
    read -p "Enter your backend URL: " BACKEND_URL
fi

echo ""

# Step 5: Test Backend
echo -e "${YELLOW}Step 5: Testing Backend...${NC}"
echo "Testing health endpoint..."

if curl -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy!${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    echo "Please check your deployment and try again."
    exit 1
fi

echo ""

# Step 6: GitHub Setup
echo -e "${YELLOW}Step 6: GitHub Setup${NC}"
echo ""
echo "To deploy the frontend, you need to push your code to GitHub."
echo ""
read -p "Have you pushed your code to GitHub? (y/n): " github_done

if [ "$github_done" != "y" ]; then
    echo ""
    echo "Please follow these steps:"
    echo "1. Create a new repository on GitHub.com"
    echo "2. Run these commands:"
    echo ""
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Smart Month-End Close System'"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/smart-month-end-close.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    read -p "Press Enter when done..."
fi

echo ""

# Step 7: Frontend Deployment Choice
echo -e "${YELLOW}Step 7: Frontend Deployment${NC}"
echo ""
echo "Choose your frontend deployment option:"
echo "1. Streamlit Community Cloud (FREE, Recommended)"
echo "2. Google Cloud Run (Pay per use)"
echo ""
read -p "Enter choice (1 or 2): " frontend_choice

if [ "$frontend_choice" = "1" ]; then
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Streamlit Community Cloud Deployment Instructions       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "1. Go to: https://streamlit.io/cloud"
    echo "2. Sign up with your GitHub account"
    echo "3. Click 'New app'"
    echo "4. Select your repository and set:"
    echo "   - Main file path: frontend/app.py"
    echo "5. Click 'Advanced settings' and add these secrets:"
    echo ""
    echo "   BACKEND_URL = \"$BACKEND_URL\""
    echo "   API_KEY = \"$API_KEY\""
    echo ""
    echo "6. Click 'Deploy!'"
    echo ""
    echo "Your app will be live at: https://your-app-name.streamlit.app"
    echo ""
    echo "For detailed instructions, see: STREAMLIT_COMMUNITY_CLOUD_GUIDE.md"
    
elif [ "$frontend_choice" = "2" ]; then
    echo ""
    echo -e "${YELLOW}Deploying frontend to Cloud Run...${NC}"
    export BACKEND_URL
    export API_KEY
    ./deploy/deploy-frontend-cloudrun.sh
    
    FRONTEND_URL=$(gcloud run services describe month-end-close-frontend \
      --region $GCP_REGION \
      --format 'value(status.url)')
    
    echo ""
    echo -e "${GREEN}✅ Frontend deployed successfully!${NC}"
    echo -e "${GREEN}Frontend URL: $FRONTEND_URL${NC}"
fi

echo ""

# Step 8: Summary
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              🎉 Deployment Complete! 🎉                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}Your Smart Month-End Close System is now live!${NC}"
echo ""
echo "📋 Deployment Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Backend API:"
echo "  URL: $BACKEND_URL"
echo "  Health: $BACKEND_URL/health"
echo "  Docs: $BACKEND_URL/docs"
echo ""
echo "Authentication:"
echo "  API Key: $API_KEY"
echo "  (Save this securely!)"
echo ""
echo "Azure OpenAI:"
echo "  Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "  Deployment: $AZURE_OPENAI_DEPLOYMENT_NAME"
echo ""
echo "Next Steps:"
echo "  1. Test backend: curl $BACKEND_URL/health"
echo "  2. Complete frontend deployment (if not done)"
echo "  3. Test file upload functionality"
echo "  4. Share the frontend URL with users"
echo ""
echo "Documentation:"
echo "  - COMPLETE_DEPLOYMENT_GUIDE.md"
echo "  - STREAMLIT_COMMUNITY_CLOUD_GUIDE.md"
echo "  - AUTHENTICATION_GUIDE.md"
echo ""
echo -e "${GREEN}Happy deploying! 🚀${NC}"
echo ""
