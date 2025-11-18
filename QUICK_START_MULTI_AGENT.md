# Quick Start - Multi-Agent System

## Prerequisites

- Python 3.9+
- Virtual environment activated
- Azure OpenAI API key configured in `.env`
- Google Cloud project set up

## 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # or .venv/bin/activate

# Install requirements
pip install -r adk-orchestrator/requirements.txt
```

## 2. Configure Environment

Ensure your `.env` file has:

```bash
# Azure OpenAI (Required for LLM features)
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GCP_REGION=us-central1
BIGQUERY_DATASET=financial_close
```

## 3. Start All Agents

```bash
./start-multi-agent-system.sh
```

You should see:
```
🚀 Starting Smart Month-End Close Multi-Agent System...

Starting agents...

📋 Starting Classifier Agent on port 8001...
📊 Starting Extractor Agent on port 8002...
✅ Starting Checklist Agent on port 8003...
📈 Starting Analytics Agent on port 8004...
💬 Starting Chatbot Agent on port 8005...
📄 Starting Report Composer Agent on port 8006...
🎯 Starting Orchestrator Agent on port 8000...

✅ All agents started successfully!
```

## 4. Verify System Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "orchestrator": "healthy",
  "agents": {
    "classifier": "healthy",
    "extractor": "healthy",
    "checklist": "healthy",
    "analytics": "healthy",
    "chatbot": "healthy",
    "report": "healthy"
  }
}
```

## 5. Test Document Upload

```bash
# Create a test CSV file
cat > test_bank_statement.csv << EOF
Date,Description,Amount,Balance
2025-01-01,Opening Balance,0,10000
2025-01-05,Deposit,5000,15000
2025-01-10,Payment,-2000,13000
2025-01-15,Deposit,3000,16000
2025-01-20,Withdrawal,-1000,15000
EOF

# Upload the document
curl -X POST http://localhost:8000/process-upload \
  -F "file=@test_bank_statement.csv" \
  -F "user_id=test_user"
```

Expected response includes:
- Classification results
- Extraction results with data quality score
- Checklist update
- Analytics with anomaly detection

## 6. Check Checklist Status

```bash
curl http://localhost:8003/status/test_user
```

## 7. Generate Report

```bash
curl -X POST http://localhost:8000/generate-report \
  -F "user_id=test_user"
```

You'll get a beautifully formatted narrative report!

## 8. Chat with AI Assistant

```bash
curl -X POST http://localhost:8000/chat \
  -F "message=What is my checklist status?" \
  -F "user_id=test_user" \
  -F "session_id=test_session"
```

## 9. View Logs

```bash
# View orchestrator logs
tail -f logs/orchestrator.log

# View all logs
tail -f logs/*.log
```

## 10. Stop All Agents

```bash
./stop-multi-agent-system.sh
```

Or press `Ctrl+C` in the terminal where agents are running.

---

## API Documentation

Each agent provides auto-generated API docs:

- Orchestrator: http://localhost:8000/docs
- Classifier: http://localhost:8001/docs
- Extractor: http://localhost:8002/docs
- Checklist: http://localhost:8003/docs
- Analytics: http://localhost:8004/docs
- Chatbot: http://localhost:8005/docs
- Report: http://localhost:8006/docs

---

## Troubleshooting

### Agents Won't Start

**Issue**: Port already in use
```bash
# Kill processes on ports
lsof -ti:8000,8001,8002,8003,8004,8005,8006 | xargs kill -9
```

**Issue**: Module not found
```bash
# Reinstall dependencies
pip install -r adk-orchestrator/requirements.txt
```

### Azure OpenAI Errors

**Issue**: Authentication failed
- Check your API key in `.env`
- Verify endpoint URL is correct
- Ensure deployment name matches

**Issue**: Model not found
- Verify deployment name in Azure portal
- Check API version compatibility

### Firestore Errors

**Issue**: Permission denied
```bash
# Authenticate with Google Cloud
gcloud auth application-default login
```

### BigQuery Errors

**Issue**: Dataset not found
```bash
# Create dataset
bq mk --dataset ${GOOGLE_CLOUD_PROJECT}:financial_close
```

---

## Next Steps

1. **Upload Real Data**: Test with your actual financial CSV files
2. **Review Reports**: Check the generated narrative reports
3. **Test Chat**: Ask questions about your data
4. **Monitor Logs**: Watch agent interactions in logs
5. **Deploy**: Follow DEPLOYMENT_GUIDE.md for Cloud Run deployment

---

## Support

- Architecture: See `MULTI_AGENT_ARCHITECTURE.md`
- Implementation: See `IMPLEMENTATION_COMPLETE.md`
- Issues: Check logs in `./logs/` directory
- API Docs: Visit http://localhost:8000/docs

---

## Success Checklist

- [ ] All 7 agents started successfully
- [ ] Health check returns all "healthy"
- [ ] Document upload works
- [ ] Classification is accurate
- [ ] Data extraction completes
- [ ] Checklist updates correctly
- [ ] Analytics detects anomalies
- [ ] Chat provides relevant answers
- [ ] Reports are narrative-style (no JSON)
- [ ] Logs show no errors

**If all checked, you're ready to go!** 🚀
