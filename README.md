# Smart Month-End Enclosure Generator

**Smart Month-End Enclosure Generator** is an AI-powered financial close automation platform that automates the month-end financial reporting process. It uses Google Cloud's Agent Development Kit (ADK) with a multi-agent architecture to process financial documents, track compliance checklists, perform analytics, and generate comprehensive reports.

## Features

- **Document Processing**: Automatic classification and extraction of CSV financial documents (bank statements, invoices, ledgers, etc.)
- **Compliance Tracking**: Real-time checklist management with completion percentage and gap detection
- **Financial Analytics**: Automated summaries, statistical analysis, and anomaly detection
- **AI-Powered Chatbot**: Natural language Q&A assistant with RAG (Retrieval-Augmented Generation) capabilities
- **Report Generation**: Comprehensive month-end close reports with executive summaries
- **Multi-Agent Architecture**: Specialized agents for classification, extraction, analytics, and more
- **Cloud-Native**: Built on Google Cloud with autoscaling and serverless deployment

## Technologies

### Backend
- **Google Agent Development Kit (ADK)**: Multi-agent orchestration framework
- **FastAPI**: REST API framework
- **Azure OpenAI**: GPT-4 for LLM capabilities
- **Vertex AI**: Embeddings for semantic search (textembedding-gecko@003)
- **Python 3.9+**: Core programming language

### Data & Storage
- **BigQuery**: Structured financial data storage
- **Firestore**: Session memory and chat history
- **Cloud Storage**: Document uploads and storage

### Frontend
- **Streamlit**: Interactive web dashboard
- **Plotly**: Data visualization

### Cloud Services
- **Cloud Run**: Serverless container deployment with autoscaling
- **Streamlit Community Cloud**: Frontend hosting (free tier)

## Architecture

The system uses a multi-agent architecture where specialized agents handle different aspects of the financial close process:

```
User → Streamlit Frontend
         ↓
    Cloud Run (ADK Orchestrator)
         ↓
    ┌────┴────┬────────┬──────────┐
    ↓         ↓        ↓          ↓
Orchestrator Chatbot Tools    Vertex AI
  Agent      Agent            (Embeddings)
    ↓         ↓        ↓          ↓
    └─────────┴────────┴──────────┘
              ↓
    ┌─────────┴─────────┐
    ↓         ↓         ↓
Cloud      BigQuery  Firestore
Storage
```

### Agents
- **Orchestrator Agent**: Master coordinator for document processing workflows
- **Chatbot Agent**: Context-aware Q&A assistant with RAG capabilities
- **Classification**: Automatic document type identification
- **Extraction**: CSV parsing and data validation
- **Analytics**: Financial analysis and anomaly detection
- **Checklist**: Progress tracking and compliance management
- **Report Composer**: Comprehensive report generation

## Quick Start

### Prerequisites

1. Google Cloud Project with billing enabled
2. Azure OpenAI deployment (GPT-4)
3. `gcloud` CLI installed and configured
4. Python 3.9+ installed

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd "Smart Month-End Enclosure Generator"
   ```

2. **Navigate to backend:**
   ```bash
   cd adk-orchestrator
   ```

3. **Create `.env` file:**
   ```bash
   # Environment
   ENVIRONMENT=production

   # Google Cloud
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_CLOUD_LOCATION=us-central1
   GCP_REGION=us-central1

   # BigQuery & Firestore
   BIGQUERY_DATASET=financial_close
   FIRESTORE_COLLECTION=sessions

   # Vertex AI Embedding
   VERTEX_EMBEDDING_MODEL=textembedding-gecko@003

   # Azure OpenAI
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-azure-openai-key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview

   # API Key (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))")
   API_KEYS=your-generated-api-key
   ```

4. **Install dependencies:**
   ```bash
   pip install uv
   uv sync
   ```

5. **Run locally:**
   ```bash
   uv run uvicorn server:app --host 0.0.0.0 --port 8080
   ```

6. **Access ADK web interface:**
   ```
   http://localhost:8080/web
   ```

### Frontend Setup

1. **Navigate to frontend:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   export BACKEND_URL=http://localhost:8080
   export API_KEY=your-api-key
   ```

4. **Run Streamlit app:**
   ```bash
   streamlit run app.py
   ```

5. **Access frontend:**
   ```
   http://localhost:8501
   ```

## Deployment

### Deploy Backend to Cloud Run

```bash
cd adk-orchestrator

gcloud run deploy month-end-close-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project) \
  --set-env-vars GCP_REGION=us-central1 \
  --set-env-vars BIGQUERY_DATASET=financial_close \
  --set-env-vars VERTEX_EMBEDDING_MODEL=textembedding-gecko@003 \
  --set-env-vars AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
  --set-env-vars AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4 \
  --set-env-vars AZURE_OPENAI_API_VERSION=2024-02-15-preview \
  --set-env-vars API_KEYS=your-api-key \
  --set-env-vars AZURE_OPENAI_API_KEY=your-azure-key
```

### Deploy Frontend to Streamlit Community Cloud

1. Push code to GitHub
2. Visit [Streamlit Cloud](https://streamlit.io/cloud)
3. Connect your repository
4. Set main file path: `frontend/app.py`
5. Add secrets:
   ```toml
   BACKEND_URL = "https://your-cloud-run-url"
   API_KEY = "your-api-key"
   ```
6. Deploy!

For detailed deployment instructions, see `QUICK_START.md` and `COMPLETE_DEPLOYMENT_GUIDE.md`.

## Usage

### Upload Documents

1. Navigate to the **Upload** page
2. Select CSV files (bank statements, invoices, ledgers, etc.)
3. Click **Process Files**
4. View classification results and extracted data

### Track Progress

1. Go to the **Checklist** page
2. View completion percentage
3. See which documents are missing
4. Track required vs optional documents

### Generate Reports

1. Navigate to the **Report** page
2. Click **Generate Report**
3. View comprehensive month-end close summary
4. Download report as JSON

### Chat with AI

1. Go to the **Chat** page
2. Ask questions about your financial data
3. Get AI-powered answers with source citations
4. View conversation history

## Project Structure

```
smart-month-end-close/
├── adk-orchestrator/          # Backend ADK agent
│   ├── month_end_agent/       # Agent implementation
│   ├── services/              # Service modules
│   ├── server.py             # FastAPI server
│   ├── Dockerfile            # Container config
│   └── pyproject.toml        # Dependencies
├── frontend/                  # Streamlit frontend
│   ├── app.py               # Main Streamlit app
│   └── requirements.txt     # Frontend dependencies
├── agents/                   # Multi-agent microservices
│   ├── orchestrator/        # Master coordinator
│   ├── classifier/          # Document classification
│   ├── extractor/           # Data extraction
│   ├── checklist/           # Checklist management
│   ├── analytics/           # Financial analytics
│   ├── chatbot/             # Q&A assistant
│   └── report/              # Report generation
├── shared/                   # Shared utilities
│   ├── models.py           # Data models
│   └── gcp_utils.py        # GCP utilities
├── sample_data/             # Test CSV files
└── deploy/                  # Deployment scripts
```

## Environment Variables

### Backend (.env)
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
- `GCP_REGION`: GCP region (e.g., us-central1)
- `BIGQUERY_DATASET`: BigQuery dataset name
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME`: Deployment name (e.g., gpt-4)
- `API_KEYS`: API key for authentication

### Frontend (Streamlit secrets)
- `BACKEND_URL`: Backend API URL
- `API_KEY`: API key for authentication

## API Endpoints

- `GET /health` - Health check
- `GET /` - Service information
- `POST /upload` - Upload single document
- `POST /upload-multiple` - Upload multiple documents
- `GET /checklist` - Get checklist status
- `POST /generate-report` - Generate month-end report
- `POST /chat` - Chat with AI assistant
- `GET /me` - Get current user info

## Testing

### Health Check
```bash
curl https://your-service-url/health
```

### Upload Document
```bash
curl -X POST https://your-service-url/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@sample_data/bank_statement.csv"
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a pull request

## Documentation

- **Quick Start**: `QUICK_START.md`
- **Complete Deployment Guide**: `COMPLETE_DEPLOYMENT_GUIDE.md`
- **Multi-Agent Architecture**: `MULTI_AGENT_ARCHITECTURE.md`
- **Testing Guide**: `TESTING_GUIDE.md`
- **Local Development**: `LOCAL_DEVELOPMENT.md`

## License

This project is licensed under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ using Google Cloud ADK, Vertex AI, and Azure OpenAI**
