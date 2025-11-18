# Multi-Agent Architecture - Smart Month-End Close System

## Overview

The Smart Month-End Close system implements a **true multi-agent architecture** where each specialized agent runs as an independent microservice. This design enables scalability, maintainability, and clear separation of concerns.

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │ (Streamlit/React)
│  Dashboard  │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│         Orchestrator Agent (Port 8000)                   │
│  Master coordinator for all workflows                    │
│  - Routes requests to specialized agents                 │
│  - Manages workflow state                                │
│  - Handles error recovery                                │
└───┬──────────┬──────────┬──────────┬──────────┬─────────┘
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Classify│ │Extract │ │Checklis│ │Analytic│ │Chatbot │
│  8001  │ │  8002  │ │  8003  │ │  8004  │ │  8005  │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
                                                  │
                                                  ▼
                                            ┌────────┐
                                            │ Report │
                                            │  8006  │
                                            └────────┘
                                                  │
                                                  ▼
                                         ┌──────────────┐
                                         │  Data Layer  │
                                         │ BigQuery     │
                                         │ Firestore    │
                                         │ Cloud Storage│
                                         └──────────────┘
```

## Agent Microservices

### 1. Orchestrator Agent (Port 8000)
**Purpose**: Master workflow coordinator

**Responsibilities**:
- Route incoming requests to appropriate agents
- Manage end-to-end workflow execution
- Handle errors and retries
- Aggregate results from multiple agents
- Provide unified API for frontend

**Key Endpoints**:
- `POST /process-upload` - Process document upload
- `POST /generate-report` - Generate month-end report
- `POST /chat` - Handle chat queries
- `GET /health` - System health check

**ADK Configuration**:
- Model: Azure OpenAI GPT-4o / Vertex AI Gemini
- Tools: orchestrate_document_processing
- Description: Master orchestration agent coordinating all workflows

---

### 2. Classifier Agent (Port 8001)
**Purpose**: Document type classification

**Responsibilities**:
- Analyze filename and content
- Classify document type (bank_statement, invoice, ledger, etc.)
- Provide confidence scores
- Generate recommendations

**Key Endpoints**:
- `POST /classify` - Classify uploaded document
- `GET /health` - Agent health check

**ADK Configuration**:
- Model: Azure OpenAI GPT-4o / Vertex AI Gemini
- Tools: classify_financial_document
- Description: Expert financial document classifier
- Instruction: Pattern matching + AI-powered classification

**Classification Categories**:
- bank_statement
- invoice_register
- general_ledger
- trial_balance
- reconciliation
- cash_flow
- schedule

---

### 3. Extractor Agent (Port 8002)
**Purpose**: CSV data extraction and validation

**Responsibilities**:
- Parse CSV files
- Validate data quality
- Detect missing values and duplicates
- Calculate quality scores
- Prepare data for storage

**Key Endpoints**:
- `POST /extract` - Extract and validate CSV data
- `GET /health` - Agent health check

**ADK Configuration**:
- Model: Azure OpenAI GPT-4o / Vertex AI Gemini
- Tools: extract_and_process_csv
- Description: Expert CSV data extraction agent
- Instruction: Parse, validate, and prepare financial data

**Data Quality Checks**:
- Missing values detection
- Duplicate row identification
- Empty column detection
- Data type validation
- Format consistency

---

### 4. Checklist Agent (Port 8003)
**Purpose**: Month-end close checklist management

**Responsibilities**:
- Track document upload status
- Calculate completion percentage
- Identify missing documents
- Provide next steps guidance
- Store status in Firestore

**Key Endpoints**:
- `POST /update` - Update checklist status
- `GET /status/{user_id}` - Get checklist status
- `GET /health` - Agent health check

**ADK Configuration**:
- Model: Azure OpenAI GPT-4o / Vertex AI Gemini
- Tools: manage_checklist
- Description: Expert checklist management agent
- Instruction: Track progress and provide guidance

**Required Documents**:
1. Bank Statement (High Priority)
2. Invoice Register (High Priority)
3. General Ledger (High Priority)
4. Bank Reconciliation (High Priority)
5. Trial Balance (Medium Priority)

---

### 5. Analytics Agent (Port 8004)
**Purpose**: Financial data analysis and anomaly detection

**Responsibilities**:
- Statistical analysis (mean, std dev, min/max)
- Anomaly detection (z-score based)
- Risk assessment
- AI-powered insights
- Generate recommendations

**Key Endpoints**:
- `POST /analyze` - Analyze financial data
- `GET /health` - Agent health check

**ADK Configuration**:
- Model: Azure OpenAI GPT-4o / Vertex AI Gemini
- Tools: analyze_financial_data_deep
- Description: Expert financial data analyst
- Instruction: Comprehensive analysis with AI insights

**Analysis Features**:
- Statistical outlier detection (z-score > 3)
- Missing data analysis
- Duplicate detection
- Risk level assessment (HIGH/MEDIUM/LOW/MINIMAL)
- AI-generated insights and recommendations

---

### 6. Chatbot Agent (Port 8005)
**Purpose**: RAG-powered Q&A assistant

**Responsibilities**:
- Answer user questions using RAG
- Search uploaded documents semantically
- Maintain conversation context
- Provide data-driven responses
- Store chat history in Firestore

**Key Endpoints**:
- `POST /chat` - Handle chat queries
- `GET /history/{session_id}` - Get chat history
- `GET /health` - Agent health check

**ADK Configuration**:
- Model: Azure OpenAI GPT-4o / Vertex AI Gemini
- Tools: answer_financial_question
- Description: Intelligent financial Q&A assistant
- Instruction: RAG-powered responses with context awareness

**Features**:
- Semantic search of uploaded documents
- Conversation history tracking
- Confidence scoring
- Source citation
- Follow-up suggestions

---

### 7. Report Composer Agent (Port 8006)
**Purpose**: LLM-powered report generation

**Responsibilities**:
- Generate comprehensive reports
- Create executive summaries
- Format narrative-style output (NO JSON/arrays)
- Provide actionable recommendations
- Support multiple report types

**Key Endpoints**:
- `POST /generate` - Generate month-end report
- `GET /health` - Agent health check

**ADK Configuration**:
- Model: Azure OpenAI GPT-4o / Vertex AI Gemini
- Tools: generate_comprehensive_report
- Description: Expert report generation agent
- Instruction: Professional narrative-style reports

**Report Types**:
- Executive: High-level summary for leadership
- Detailed: Complete analysis for accounting team
- Audit: Compliance-focused documentation

**Report Sections**:
1. Executive Summary
2. Document Processing Summary
3. Checklist Status
4. Financial Analysis
5. Anomalies and Issues
6. Risk Assessment
7. Recommendations
8. Next Steps

---

## Workflow Execution

### Document Upload Workflow

```
1. User uploads CSV file
   ↓
2. Orchestrator receives request
   ↓
3. Classifier Agent → Identifies document type
   ↓
4. Extractor Agent → Parses and validates data
   ↓
5. Checklist Agent → Updates completion status
   ↓
6. Analytics Agent → Analyzes data for anomalies
   ↓
7. Orchestrator → Returns aggregated results
```

### Report Generation Workflow

```
1. User requests report
   ↓
2. Orchestrator gathers data:
   - Checklist status from Checklist Agent
   - Documents from BigQuery
   - Analytics from Analytics Agent
   ↓
3. Report Composer Agent → Generates narrative report
   ↓
4. Orchestrator → Returns formatted report
```

### Chat Workflow

```
1. User asks question
   ↓
2. Orchestrator forwards to Chatbot Agent
   ↓
3. Chatbot Agent:
   - Searches documents (RAG)
   - Retrieves conversation history
   - Generates AI response
   ↓
4. Orchestrator → Returns answer with sources
```

---

## Technology Stack

### Core Technologies
- **Google ADK**: Agent orchestration framework
- **Azure OpenAI**: GPT-4o for LLM capabilities
- **FastAPI**: Microservice framework
- **LiteLLM**: Unified LLM interface

### Data Layer
- **BigQuery**: Structured data storage
- **Firestore**: Session and checklist storage
- **Cloud Storage**: Raw file storage
- **Vertex AI**: Embeddings for RAG

### Deployment
- **Cloud Run**: Containerized microservices
- **Docker**: Container images
- **Pub/Sub**: Async messaging (future)

---

## Running the System

### Start All Agents
```bash
./start-multi-agent-system.sh
```

This starts all 7 agents on ports 8000-8006.

### Stop All Agents
```bash
./stop-multi-agent-system.sh
```

### Check System Health
```bash
curl http://localhost:8000/health
```

### View Logs
```bash
tail -f logs/orchestrator.log
tail -f logs/classifier.log
# etc.
```

---

## API Usage Examples

### Upload Document
```bash
curl -X POST http://localhost:8000/process-upload \
  -F "file=@bank_statement.csv" \
  -F "user_id=user123"
```

### Generate Report
```bash
curl -X POST http://localhost:8000/generate-report \
  -F "user_id=user123"
```

### Chat Query
```bash
curl -X POST http://localhost:8000/chat \
  -F "message=What is my total?" \
  -F "user_id=user123" \
  -F "session_id=session456"
```

---

## Advantages of Multi-Agent Architecture

### 1. **Scalability**
- Each agent can scale independently
- High-traffic agents can have more instances
- Resource allocation per agent needs

### 2. **Maintainability**
- Clear separation of concerns
- Easy to update individual agents
- Independent testing and deployment

### 3. **Resilience**
- Failure isolation (one agent failure doesn't crash system)
- Graceful degradation
- Easy to implement retries

### 4. **Flexibility**
- Easy to add new agents
- Can swap out implementations
- Support multiple LLM providers

### 5. **Observability**
- Per-agent logging and monitoring
- Clear performance metrics
- Easy debugging

---

## Future Enhancements

1. **Pub/Sub Integration**: Async processing for long-running tasks
2. **Agent Mesh**: Service mesh for advanced routing
3. **Caching Layer**: Redis for frequently accessed data
4. **Load Balancing**: Multiple instances per agent
5. **API Gateway**: Unified entry point with rate limiting
6. **Monitoring**: Prometheus + Grafana dashboards
7. **Tracing**: Distributed tracing with OpenTelemetry

---

## Deployment to Cloud Run

Each agent will be deployed as a separate Cloud Run service:

```
orchestrator-agent    → cloud-run-service-1
classifier-agent      → cloud-run-service-2
extractor-agent       → cloud-run-service-3
checklist-agent       → cloud-run-service-4
analytics-agent       → cloud-run-service-5
chatbot-agent         → cloud-run-service-6
report-composer-agent → cloud-run-service-7
```

See `DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

---

## Conclusion

This multi-agent architecture provides a robust, scalable foundation for the Smart Month-End Close system. Each agent is a specialized expert in its domain, working together through the orchestrator to deliver comprehensive financial close automation.
