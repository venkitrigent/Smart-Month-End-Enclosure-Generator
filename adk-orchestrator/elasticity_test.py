"""
Elasticity test for Month-End Close ADK Agent
Tests system behavior under load
"""

import random
import uuid
from locust import HttpUser, task, between


class MonthEndCloseUser(HttpUser):
    """Simulated user for elasticity testing"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = f"user_{uuid.uuid4()}"
        self.session_id = f"session_{uuid.uuid4()}"
        
        # Create session
        session_data = {"state": {"user_type": "elasticity_test"}}
        self.client.post(
            f"/apps/orchestrator_agent/users/{self.user_id}/sessions/{self.session_id}",
            headers={"Content-Type": "application/json"},
            json=session_data,
        )
    
    @task(3)
    def test_document_processing(self):
        """Test document upload and processing workflow"""
        queries = [
            "I uploaded a bank statement CSV. Can you process it?",
            "What's the status of my month-end close checklist?",
            "Analyze the financial data from my latest upload",
            "Show me any anomalies in the bank statement",
        ]
        
        message_data = {
            "app_name": "orchestrator_agent",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": random.choice(queries)}]
            }
        }
        
        self.client.post(
            "/run",
            headers={"Content-Type": "application/json"},
            json=message_data,
        )
    
    @task(2)
    def test_chatbot_queries(self):
        """Test chatbot Q&A capabilities"""
        questions = [
            "What documents are still missing?",
            "What's my completion percentage?",
            "Explain the month-end close process",
            "What are the required documents?",
        ]
        
        message_data = {
            "app_name": "chatbot_agent",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": random.choice(questions)}]
            }
        }
        
        self.client.post(
            "/run",
            headers={"Content-Type": "application/json"},
            json=message_data,
        )
    
    @task(1)
    def health_check(self):
        """Test health endpoint"""
        self.client.get("/health")
