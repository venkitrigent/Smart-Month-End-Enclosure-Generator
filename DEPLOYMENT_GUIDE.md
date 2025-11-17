# Deployment Guide - Smart Month-End Close

## Architecture Overview

Based on Google Cloud Run ADK deployment best practices, this project uses:

1. **ADK Agent on Cloud Run** - Main service with Vertex AI Gemini
2. **Multi-agent orchestration** - Specialized agents for different tasks
3. **Autoscaling** - Handles variable workloads efficiently

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Required APIs** (enabled automatically by deployment script):
   - Cloud Run API
   - Artifact Registry API
   - Cloud Build API
   - Vertex AI API

## Step-by-Step Deployment

### 1. Authenticate and Set Project

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Set default region
gcloud config set run/region us-central1
```

### 2. Deploy ADK Agent

```bash
# Navigate to deploy directory
cd deploy

# Make script executable
chmod +x deploy-adk-agent.sh

# Set environment variables (optional)
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1

# Deploy
./deploy-adk-agent.sh
```

The script will:
- Enable required APIs
- Build container with Cloud Build
- Deploy to Cloud Run with optimal settings
- Output service URL

### 3. Verify Deployment

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe month-end-close-agent \
  --region=us-central1 \
  --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Expected response:
# {"status":"healthy","service":"month-end-close-agent","version":"1.0.0"}
```

### 4. Access Web Interface

Open in browser:
```
https://your-service-url/web
```

You'll see the ADK web interface where you can:
- Upload CSV files
- Chat with the agent
- View processing results
- Check checklist status

## Configuration Details

### Cloud Run Settings

The deployment uses these optimized settings:

```bash
--memory 4Gi              # Sufficient for CSV processing
--cpu 2                   # 2 vCPUs for parallel processing
--max-instances 5         # Scale up to 5 instances
--min-instances 0         # Scale to zero when idle
--concurrency 50          # 50 requests per instance
--timeout 300             # 5 minute timeout
```

### Environment Variables

Set in deployment:
- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID
- `GOOGLE_CLOUD_LOCATION` - Region (us-central1)
- `GEMINI_MODEL` - Vertex AI model (gemini-2.0-flash-exp)

### Cost Optimization

- **Scale to zero**: No charges when idle
- **CPU-only**: No GPU needed for this workload
- **Efficient concurrency**: Handles multiple requests per instance

Estimated cost: **~$0.10-0.50/hour** under moderate load

## Testing the Deployment

### 1. Manual Testing

Upload sample CSV files through the web UI:
```bash
# Sample files are in sample_data/
- bank_statement.csv
- invoice_register.csv
```

### 2. Elasticity Testing

Test autoscaling behavior:

```bash
cd adk-orchestrator

# Install dependencies
uv sync

# Run load test
uv run locust -f elasticity_test.py \
  -H $SERVICE_URL \
  --headless \
  -t 60s \
  -u 20 \
  -r 5
```

Parameters:
- `-t 60s` - Run for 60 seconds
- `-u 20` - Simulate 20 users
- `-r 5` - Spawn 5 users per second

### 3. Monitor in Console

Watch autoscaling in action:
1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on `month-end-close-agent`
3. View **Metrics** tab during load test
4. Observe instance count increasing

## Updating the Deployment

### Update Agent Code

```bash
# Make changes to adk-orchestrator/month_end_agent/agent.py

# Redeploy
cd deploy
./deploy-adk-agent.sh
```

### Update Environment Variables

```bash
gcloud run services update month-end-close-agent \
  --region us-central1 \
  --set-env-vars NEW_VAR=value
```

## Troubleshooting

### Check Logs

```bash
gcloud run services logs read month-end-close-agent \
  --region us-central1 \
  --limit 50
```

### Common Issues

**Issue**: "Permission denied" errors
**Solution**: Ensure APIs are enabled and you have necessary IAM roles

**Issue**: "Service not found"
**Solution**: Check region matches deployment region

**Issue**: Slow cold starts
**Solution**: Consider setting `--min-instances 1` for production

## Security Best Practices

For production deployment:

1. **Remove `--allow-unauthenticated`**:
```bash
gcloud run services update month-end-close-agent \
  --region us-central1 \
  --no-allow-unauthenticated
```

2. **Add authentication**:
- Use Cloud IAM
- Implement Firebase Auth
- Add API keys

3. **Use Secret Manager** for sensitive data:
```bash
gcloud run services update month-end-close-agent \
  --region us-central1 \
  --set-secrets API_KEY=api-key:latest
```

## Cleanup

To avoid charges, delete resources:

```bash
# Delete Cloud Run service
gcloud run services delete month-end-close-agent \
  --region us-central1

# Delete container images (optional)
gcloud artifacts repositories delete cloud-run-source-deploy \
  --location us-central1
```

## Next Steps

1. **Add BigQuery integration** for persistent storage
2. **Implement Firestore** for session management
3. **Add embeddings** for RAG-based Q&A
4. **Create custom frontend** with Streamlit
5. **Set up CI/CD** with Cloud Build

## Resources

- [ADK Documentation](https://google.github.io/adk-docs/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [Sample Codelab](https://codelabs.developers.google.com/codelabs/cloud-run/how-to-connect-adk-to-deployed-cloud-run-llm)
