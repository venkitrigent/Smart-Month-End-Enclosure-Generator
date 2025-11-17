import os
from google.cloud import storage, bigquery, firestore
from google.cloud import aiplatform

class GCPClient:
    def __init__(self):
        self.project_id = os.getenv('GCP_PROJECT_ID')
        self.region = os.getenv('GCP_REGION', 'us-central1')
        self.bucket_name = os.getenv('GCS_BUCKET_NAME')
        
        self.storage_client = storage.Client(project=self.project_id)
        self.bq_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        
        aiplatform.init(project=self.project_id, location=self.region)
    
    def upload_to_gcs(self, file_content, destination_blob_name):
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_content)
        return f"gs://{self.bucket_name}/{destination_blob_name}"
    
    def insert_to_bigquery(self, dataset_id, table_id, rows):
        table_ref = f"{self.project_id}.{dataset_id}.{table_id}"
        errors = self.bq_client.insert_rows_json(table_ref, rows)
        return errors
    
    def save_to_firestore(self, collection, document_id, data):
        doc_ref = self.firestore_client.collection(collection).document(document_id)
        doc_ref.set(data)
    
    def get_from_firestore(self, collection, document_id):
        doc_ref = self.firestore_client.collection(collection).document(document_id)
        return doc_ref.get().to_dict()

gcp_client = GCPClient()
