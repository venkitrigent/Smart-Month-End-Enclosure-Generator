# Orchestrator Agent Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY agents/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ /app/shared/

# Copy agent code
COPY agents/orchestrator/ /app/

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
