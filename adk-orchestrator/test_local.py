"""
Quick local test for the agent
"""
import os
os.environ["GOOGLE_CLOUD_PROJECT"] = "aimonthendenclosuregenerator"
os.environ["GCP_REGION"] = "us-central1"

from month_end_agent.agent import classify_document

# Test classification
result = classify_document("bank_statement.csv")
print("Classification result:", result)
print("\n✅ Agent tools working!")
