# Local Development Guide

## Prerequisites

Before you start, make sure you have:

1. **Python 3.11 or higher**
   ```bash
   python3 --version
   ```

2. **Google Cloud SDK** (gcloud)
   ```bash
   gcloud --version
   ```

3. **Google Cloud Project** with billing enabled

4. **uv package manager** (we'll install this)

## Step-by-Step Local Setup

### Step 1: Install uv Package Manager

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Verify installation
uv --version
```

### Step 2: Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set your project (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Set application default credentials (important for local testing)
gcloud auth application-default login

# Verify your project
gcloud config get-value project
```

### Step 3: Enable Required APIs

```bash
# Enable Vertex AI API (required for Gemini)
gcloud services enable aiplatform.googleapis.com

# Enable other APIs (optional for full functionality)
gcloud services enable \
  storage.googleapis.com \
  bigquery.googleapis.com \
  firestore.googleapis.com
```

### Step 4: Set Up Environment Variables

```bash
# Navigate to the ADK orchestrator directory
cd adk-orchestrator

# Copy the example environment file
cp .env.example .env

# Edit the .env file with your actual values
# You can use any text editor
nano .env
# or
code .env
```

Edit `.env` to include:
```bash
GOOGLE_CLOUD_PROJECT=your-actual-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GCP_REGION=us-central1
GEMINI_MODEL=gemini-2.0-flash-exp
GCS_BUCKET_NAME=month-end-close-uploads
BIGQUERY_DATASET=financial_close
FIRESTORE_COLLECTION=sessions
```

### Step 5: Install Dependencies

```bash
# Still in adk-orchestrator directory
# This will create a virtual environment and install all dependencies
uv sync

# This creates a .venv directory with all packages
```

### Step 6: Run the ADK Agent Locally

```bash
# Run the server
uv run uvicorn server:app --host 0.0.0.0 --port 8080 --reload

# The --reload flag enables auto-reload on code changes
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 7: Access the Application

Open your browser and navigate to:

1. **Web UI**: http://localhost:8080/web
   - This is the ADK interactive interface
   - You can chat with the agent here

2. **API Documentation**: http://localhost:8080/docs
   - Interactive API documentation (Swagger UI)
   - Test endpoints directly

3. **Health Check**: http://localhost:8080/health
   - Simple health check endpoint

## Testing the Agent Locally

### Test 1: Health Check

```bash
# In a new terminal window
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "month-end-close-agent",
  "version": "1.0.0"
}
```

### Test 2: Web Interface

1. Go to http://localhost:8080/web
2. You should see the ADK chat interface
3. Try these test messages:

**Test Message 1**: Document Classification
```
I have a file called "bank_statement_november.csv". What type of document is this?
```

**Test Message 2**: Checklist Status
```
What's the status of my month-end close checklist?
```

**Test Message 3**: General Question
```
What documents do I need for month-end close?
```

### Test 3: Using the API Directly

```bash
# Test the orchestrator agent
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "orchestrator_agent",
    "user_id": "test_user",
    "session_id": "test_session_123",
    "new_message": {
      "role": "user",
      "parts": [{"text": "What documents are required for month-end close?"}]
    }
  }'
```

## Understanding the Code Structure

### Key Files to Explore

1. **`month_end_agent/agent.py`** - Main agent definitions
   ```bash
   # Open in your editor
   code month_end_agent/agent.py
   ```
   
   This file contains:
   - Tool definitions (classify_document, extract_csv_data, etc.)
   - Agent configurations (orchestrator_agent, chatbot_agent)
   - Instructions for each agent

2. **`server.py`** - FastAPI server setup
   ```bash
   code server.py
   ```
   
   This file:
   - Creates the FastAPI app with ADK integration
   - Defines health check endpoint
   - Configures the web interface

3. **`.env`** - Environment configuration
   - Contains your GCP project settings
   - Model configuration
   - Storage settings

## Modifying the Agent

### Example: Add a New Tool

Edit `month_end_agent/agent.py`:

```python
# Add this new tool
@Tool
def calculate_total_amount(amounts: list) -> float:
    """
    Calculate total from a list of amounts.
    
    Args:
        amounts: List of numeric amounts
        
    Returns:
        Total sum
    """
    return sum(amounts)

# Then add it to the orchestrator_agent tools list:
orchestrator_agent = Agent(
    # ... existing config ...
    tools=[
        classify_document,
        extract_csv_data,
        check_checklist_status,
        analyze_financial_data,
        calculate_total_amount,  # Add your new tool here
    ]
)
```

Save the file, and the server will auto-reload (if you used `--reload` flag).

## Testing with Sample Data

### Create a Test CSV File

```bash
# Create a test directory
mkdir -p test_data

# Create a simple bank statement CSV
cat > test_data/test_bank_statement.csv << 'EOF'
Date,Description,Type,Amount,Balance
2024-11-01,Opening Balance,Credit,50000.00,50000.00
2024-11-02,Vendor Payment,Debit,-5000.00,45000.00
2024-11-03,Customer Receipt,Credit,12000.00,57000.00
EOF
```

### Test Document Processing

In the web UI (http://localhost:8080/web), try:

```
I have uploaded a file called "test_bank_statement.csv" with the following content:
Date,Description,Type,Amount,Balance
2024-11-01,Opening Balance,Credit,50000.00,50000.00
2024-11-02,Vendor Payment,Debit,-5000.00,45000.00

Can you classify and analyze this document?
```

## Troubleshooting

### Issue 1: "Module not found" errors

**Solution**: Make sure you're running commands with `uv run`:
```bash
# Wrong
python server.py

# Correct
uv run uvicorn server:app --host 0.0.0.0 --port 8080
```

### Issue 2: "Authentication error" or "Permission denied"

**Solution**: Re-authenticate with application default credentials:
```bash
gcloud auth application-default login
```

### Issue 3: "Vertex AI API not enabled"

**Solution**: Enable the API:
```bash
gcloud services enable aiplatform.googleapis.com
```

### Issue 4: Port 8080 already in use

**Solution**: Use a different port:
```bash
uv run uvicorn server:app --host 0.0.0.0 --port 8081
```

Then access at http://localhost:8081/web

### Issue 5: "Model not found" or Gemini errors

**Solution**: Check your model name in `.env`:
```bash
# Try different model names
GEMINI_MODEL=gemini-2.0-flash-exp
# or
GEMINI_MODEL=gemini-1.5-flash
# or
GEMINI_MODEL=gemini-1.5-pro
```

## Viewing Logs

The server outputs logs to the terminal. Watch for:

```
INFO:     127.0.0.1:xxxxx - "POST /run HTTP/1.1" 200 OK
```

For more detailed logs, set log level:
```bash
uv run uvicorn server:app --host 0.0.0.0 --port 8080 --log-level debug
```

## Running Tests

### Run Elasticity Test Locally

```bash
# In adk-orchestrator directory
uv run locust -f elasticity_test.py \
  -H http://localhost:8080 \
  --headless \
  -t 30s \
  -u 5 \
  -r 1
```

This will:
- Simulate 5 users
- Run for 30 seconds
- Show request statistics

## Next Steps After Local Testing

Once everything works locally:

1. **Review the code** - Understand how agents and tools work
2. **Customize agents** - Modify instructions or add new tools
3. **Test thoroughly** - Try different scenarios
4. **Deploy to Cloud Run** - Follow `DEPLOYMENT_GUIDE.md`

## Quick Reference Commands

```bash
# Start server
cd adk-orchestrator
uv run uvicorn server:app --host 0.0.0.0 --port 8080 --reload

# Test health
curl http://localhost:8080/health

# View web UI
open http://localhost:8080/web

# View API docs
open http://localhost:8080/docs

# Run tests
uv run locust -f elasticity_test.py -H http://localhost:8080 --headless -t 30s -u 5 -r 1

# Stop server
# Press CTRL+C in the terminal running the server
```

## Understanding What's Happening

When you send a message through the web UI:

1. **User sends message** → FastAPI receives it
2. **ADK routes to agent** → Based on app_name (orchestrator_agent or chatbot_agent)
3. **Agent processes** → Uses Vertex AI Gemini to understand intent
4. **Tools are called** → Agent decides which tools to use (classify_document, etc.)
5. **Response generated** → Gemini creates natural language response
6. **User sees result** → Displayed in web UI

## Tips for Demo Preparation

1. **Test all scenarios** before your presentation
2. **Prepare sample questions** that showcase different features
3. **Have backup responses** ready if API is slow
4. **Screenshot the web UI** for your presentation
5. **Note the response times** to discuss performance

## Getting Help

If you encounter issues:

1. Check the terminal logs for error messages
2. Verify your `.env` file has correct values
3. Ensure APIs are enabled in your GCP project
4. Check `PROJECT_SUMMARY.md` for architecture details
5. Review `DEPLOYMENT_GUIDE.md` for configuration options

---

**You're now ready to develop and test locally!** 🚀

Once you're comfortable with local testing, proceed to Cloud Run deployment for your demo.
