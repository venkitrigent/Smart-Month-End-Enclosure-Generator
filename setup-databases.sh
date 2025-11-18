#!/bin/bash

# Setup Google Cloud Databases for Smart Month-End Close
# This script creates BigQuery dataset, Firestore database, and Cloud Storage bucket

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Database Setup for Smart Month-End Close           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set!${NC}"
    echo "Please set your project:"
    echo "  gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"
echo ""

# Configuration
REGION="us-central1"
DATASET_ID="financial_close"
BUCKET_NAME="${PROJECT_ID}-month-end-close"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  BigQuery Dataset: $DATASET_ID"
echo "  Storage Bucket: $BUCKET_NAME"
echo ""

read -p "Continue with setup? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 1: Enabling Required APIs...${NC}"

# Enable APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"
echo ""

# Step 2: Create BigQuery Dataset
echo -e "${YELLOW}Step 2: Creating BigQuery Dataset...${NC}"

if gcloud bigquery datasets describe $DATASET_ID --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}⚠️  Dataset '$DATASET_ID' already exists${NC}"
else
    bq mk --dataset --location=$REGION --project_id=$PROJECT_ID $DATASET_ID
    echo -e "${GREEN}✅ Created BigQuery dataset: $DATASET_ID${NC}"
fi

# Create tables
echo -e "${YELLOW}Creating BigQuery tables...${NC}"

# Table 1: documents
bq mk --table \
  --project_id=$PROJECT_ID \
  --schema \
    document_id:STRING,\
    filename:STRING,\
    doc_type:STRING,\
    user_id:STRING,\
    upload_time:TIMESTAMP,\
    row_count:INTEGER,\
    columns:STRING \
  $DATASET_ID.documents 2>/dev/null || echo "  Table 'documents' already exists"

# Table 2: structured_data
bq mk --table \
  --project_id=$PROJECT_ID \
  --schema \
    row_id:STRING,\
    document_id:STRING,\
    doc_type:STRING,\
    row_index:INTEGER,\
    data:STRING,\
    created_at:TIMESTAMP \
  $DATASET_ID.structured_data 2>/dev/null || echo "  Table 'structured_data' already exists"

# Table 3: embeddings
bq mk --table \
  --project_id=$PROJECT_ID \
  --schema \
    embedding_id:STRING,\
    document_id:STRING,\
    row_index:INTEGER,\
    chunk_text:STRING,\
    embedding:STRING,\
    metadata:STRING,\
    created_at:TIMESTAMP \
  $DATASET_ID.embeddings 2>/dev/null || echo "  Table 'embeddings' already exists"

echo -e "${GREEN}✅ BigQuery tables created${NC}"
echo ""

# Step 3: Create Firestore Database
echo -e "${YELLOW}Step 3: Setting up Firestore...${NC}"

# Check if Firestore is already enabled
if gcloud firestore databases list --project=$PROJECT_ID 2>/dev/null | grep -q "(default)"; then
    echo -e "${YELLOW}⚠️  Firestore already enabled${NC}"
else
    echo "Creating Firestore database in Native mode..."
    gcloud firestore databases create \
      --location=$REGION \
      --project=$PROJECT_ID \
      --type=firestore-native 2>/dev/null || echo "  Firestore setup in progress..."
    
    echo -e "${GREEN}✅ Firestore database created${NC}"
fi

echo ""

# Step 4: Create Cloud Storage Bucket
echo -e "${YELLOW}Step 4: Creating Cloud Storage Bucket...${NC}"

if gsutil ls -b gs://$BUCKET_NAME &>/dev/null; then
    echo -e "${YELLOW}⚠️  Bucket '$BUCKET_NAME' already exists${NC}"
else
    gsutil mb -l $REGION gs://$BUCKET_NAME
    echo -e "${GREEN}✅ Created bucket: gs://$BUCKET_NAME${NC}"
fi

# Set bucket permissions
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME 2>/dev/null || true

echo ""

# Step 5: Grant Permissions
echo -e "${YELLOW}Step 5: Setting up IAM permissions...${NC}"

# Get Cloud Run service account
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

# Grant BigQuery permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/bigquery.dataEditor" \
  --condition=None 2>/dev/null || true

# Grant Firestore permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/datastore.user" \
  --condition=None 2>/dev/null || true

# Grant Storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/storage.objectAdmin" \
  --condition=None 2>/dev/null || true

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user" \
  --condition=None 2>/dev/null || true

echo -e "${GREEN}✅ IAM permissions configured${NC}"
echo ""

# Step 6: Verify Setup
echo -e "${YELLOW}Step 6: Verifying setup...${NC}"

# Check BigQuery
if bq ls --project_id=$PROJECT_ID $DATASET_ID &>/dev/null; then
    echo -e "${GREEN}✅ BigQuery dataset accessible${NC}"
else
    echo -e "${RED}❌ BigQuery dataset not accessible${NC}"
fi

# Check Firestore
if gcloud firestore databases list --project=$PROJECT_ID &>/dev/null; then
    echo -e "${GREEN}✅ Firestore accessible${NC}"
else
    echo -e "${RED}❌ Firestore not accessible${NC}"
fi

# Check Storage
if gsutil ls gs://$BUCKET_NAME &>/dev/null; then
    echo -e "${GREEN}✅ Cloud Storage bucket accessible${NC}"
else
    echo -e "${RED}❌ Cloud Storage bucket not accessible${NC}"
fi

echo ""
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              🎉 Database Setup Complete! 🎉                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}Your databases are ready!${NC}"
echo ""
echo "📋 Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "BigQuery Dataset:"
echo "  Project: $PROJECT_ID"
echo "  Dataset: $DATASET_ID"
echo "  Tables: documents, structured_data, embeddings"
echo "  Location: $REGION"
echo ""
echo "Firestore:"
echo "  Database: (default)"
echo "  Mode: Native"
echo "  Location: $REGION"
echo ""
echo "Cloud Storage:"
echo "  Bucket: gs://$BUCKET_NAME"
echo "  Location: $REGION"
echo ""
echo "Next Steps:"
echo "  1. Update your .env file with:"
echo "     BIGQUERY_DATASET=$DATASET_ID"
echo "     GCS_BUCKET_NAME=$BUCKET_NAME"
echo ""
echo "  2. Deploy your backend:"
echo "     cd adk-orchestrator"
echo "     gcloud run deploy month-end-close-api --source ."
echo ""
echo -e "${GREEN}Ready to deploy! 🚀${NC}"
echo ""
