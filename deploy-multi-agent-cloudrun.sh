#!/bin/bash

# Deploy Multi-Agent System to Cloud Run (using --source flag like your previous deployment)

set -e

echo "🚀 Deploying Smart Month-End Close Multi-Agent System to Cloud Run"
echo ""

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-aimonthendenclosuregenerator}"
REGION="${GCP_REGION:-us-central1}"
BIGQUERY_DATASET="${BIGQUERY_DATASET:-financial_close}"
VERTEX_EMBEDDING_MODEL="${VERTEX_EMBEDDING_MODEL:-textembedding-gecko@003}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-2.0-flash-exp}"
API_KEYS="${API_KEYS:-TgT8q6IDgG5SE-FRvk0qiL-JUjL-AZLbLGjT65IGqfc}"

echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo ""

# Load environment variables
if [ -f "adk-orchestrator/.env" ]; then
    export $(cat adk-orchestrator/.env | grep -v '^#' | xargs)
fi

# Function to deploy agent using --source
deploy_agent() {
    local SERVICE_NAME=$1
    local SOURCE_DIR=$2
    
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "Deploying ${SERVICE_NAME}..."
    echo "═══════════════════════════════════════════════════════════════"
    
    cd $SOURCE_DIR
    
    gcloud run deploy ${SERVICE_NAME} \
        --source . \
        --region $REGION \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --max-instances 10 \
        --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
        --set-env-vars GCP_REGION=$REGION \
        --set-env-vars BIGQUERY_DATASET=$BIGQUERY_DATASET \
        --set-env-vars VERTEX_EMBEDDING_MODEL=$VERTEX_EMBEDDING_MODEL \
        --set-env-vars GEMINI_MODEL=$GEMINI_MODEL \
        --set-env-vars ENVIRONMENT=production \
        --set-env-vars API_KEYS=$API_KEYS \
        --set-env-vars AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
        --set-env-vars AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}" \
        --set-env-vars AZURE_OPENAI_DEPLOYMENT_NAME="${AZURE_OPENAI_DEPLOYMENT_NAME}" \
        --set-env-vars AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION}"
    
    SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
        --region $REGION \
        --format 'value(status.url)')
    
    cd - > /dev/null
    
    echo "✅ ${SERVICE_NAME} deployed: $SERVICE_URL"
    echo "$SERVICE_URL"
}

# Deploy agents
echo "Starting deployment..."

CLASSIFIER_URL=$(deploy_agent "classifier-agent" "agents/classifier")
EXTRACTOR_URL=$(deploy_agent "extractor-agent" "agents/extractor")
CHECKLIST_URL=$(deploy_agent "checklist-agent" "agents/checklist")
ANALYTICS_URL=$(deploy_agent "analytics-agent" "agents/analytics")
CHATBOT_URL=$(deploy_agent "chatbot-agent" "agents/chatbot")
REPORT_URL=$(deploy_agent "report-agent" "agents/report")

# Deploy orchestrator with agent URLs
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Deploying orchestrator-agent..."
echo "═══════════════════════════════════════════════════════════════"

cd agents/orchestrator

gcloud run deploy orchestrator-agent \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --set-env-vars GCP_REGION=$REGION \
    --set-env-vars BIGQUERY_DATASET=$BIGQUERY_DATASET \
    --set-env-vars VERTEX_EMBEDDING_MODEL=$VERTEX_EMBEDDING_MODEL \
    --set-env-vars GEMINI_MODEL=$GEMINI_MODEL \
    --set-env-vars ENVIRONMENT=production \
    --set-env-vars API_KEYS=$API_KEYS \
    --set-env-vars AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY}" \
    --set-env-vars AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT}" \
    --set-env-vars AZURE_OPENAI_DEPLOYMENT_NAME="${AZURE_OPENAI_DEPLOYMENT_NAME}" \
    --set-env-vars AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION}" \
    --set-env-vars CLASSIFIER_URL=$CLASSIFIER_URL \
    --set-env-vars EXTRACTOR_URL=$EXTRACTOR_URL \
    --set-env-vars CHECKLIST_URL=$CHECKLIST_URL \
    --set-env-vars ANALYTICS_URL=$ANALYTICS_URL \
    --set-env-vars CHATBOT_URL=$CHATBOT_URL \
    --set-env-vars REPORT_URL=$REPORT_URL

ORCHESTRATOR_URL=$(gcloud run services describe orchestrator-agent \
    --region $REGION \
    --format 'value(status.url)')

cd - > /dev/null

echo "✅ orchestrator-agent deployed: $ORCHESTRATOR_URL"

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Orchestrator:    $ORCHESTRATOR_URL"
echo "📋 Classifier:      $CLASSIFIER_URL"
echo "📊 Extractor:       $EXTRACTOR_URL"
echo "✅ Checklist:       $CHECKLIST_URL"
echo "📈 Analytics:       $ANALYTICS_URL"
echo "💬 Chatbot:         $CHATBOT_URL"
echo "📄 Report:          $REPORT_URL"
echo ""
echo "Test: curl ${ORCHESTRATOR_URL}/health"
echo ""

# Save URLs
cat > deployed_urls.txt << EOF
ORCHESTRATOR_URL=$ORCHESTRATOR_URL
CLASSIFIER_URL=$CLASSIFIER_URL
EXTRACTOR_URL=$EXTRACTOR_URL
CHECKLIST_URL=$CHECKLIST_URL
ANALYTICS_URL=$ANALYTICS_URL
CHATBOT_URL=$CHATBOT_URL
REPORT_URL=$REPORT_URL
EOF

echo "📝 URLs saved to deployed_urls.txt"
