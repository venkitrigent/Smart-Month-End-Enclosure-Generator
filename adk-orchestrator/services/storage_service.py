"""
Storage service for BigQuery and Firestore integration
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from google.cloud import bigquery, firestore
import pandas as pd


class StorageService:
    """Handles all data storage operations"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.dataset_id = os.getenv('BIGQUERY_DATASET', 'financial_close')
        
        # Initialize clients
        self.bq_client = bigquery.Client(project=self.project_id)
        self.firestore_client = firestore.Client(project=self.project_id)
        
        # Ensure dataset exists
        self._ensure_dataset()
        self._ensure_tables()
    
    def _ensure_dataset(self):
        """Create BigQuery dataset if it doesn't exist"""
        dataset_ref = f"{self.project_id}.{self.dataset_id}"
        try:
            self.bq_client.get_dataset(dataset_ref)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            self.bq_client.create_dataset(dataset, exists_ok=True)
    
    def _ensure_tables(self):
        """Create required BigQuery tables"""
        
        # Documents table
        documents_schema = [
            bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("filename", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("doc_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("upload_time", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("row_count", "INTEGER"),
            bigquery.SchemaField("columns", "STRING", mode="REPEATED"),
        ]
        self._create_table("documents", documents_schema)
        
        # Structured data table
        data_schema = [
            bigquery.SchemaField("record_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("doc_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("row_index", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("data", "JSON", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        self._create_table("structured_data", data_schema)
        
        # Embeddings table
        embeddings_schema = [
            bigquery.SchemaField("embedding_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("document_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("row_index", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("chunk_text", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("embedding", "FLOAT64", mode="REPEATED"),
            bigquery.SchemaField("metadata", "JSON"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        self._create_table("embeddings", embeddings_schema)
    
    def _create_table(self, table_name: str, schema: List[bigquery.SchemaField]):
        """Create a BigQuery table if it doesn't exist"""
        table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
        try:
            self.bq_client.get_table(table_ref)
        except Exception:
            table = bigquery.Table(table_ref, schema=schema)
            self.bq_client.create_table(table, exists_ok=True)
    
    # BigQuery operations
    def save_document(self, document_id: str, filename: str, doc_type: str, 
                     user_id: str, row_count: int, columns: List[str]) -> bool:
        """Save document metadata to BigQuery"""
        table_ref = f"{self.project_id}.{self.dataset_id}.documents"
        
        rows = [{
            "document_id": document_id,
            "filename": filename,
            "doc_type": doc_type,
            "user_id": user_id,
            "upload_time": datetime.utcnow().isoformat(),
            "row_count": row_count,
            "columns": columns,
        }]
        
        errors = self.bq_client.insert_rows_json(table_ref, rows)
        return len(errors) == 0
    
    def save_structured_data(self, document_id: str, doc_type: str, 
                            data: List[Dict[str, Any]]) -> bool:
        """Save parsed CSV data to BigQuery"""
        table_ref = f"{self.project_id}.{self.dataset_id}.structured_data"
        
        rows = []
        for idx, row_data in enumerate(data):
            rows.append({
                "record_id": f"{document_id}_{idx}",
                "document_id": document_id,
                "doc_type": doc_type,
                "row_index": idx,
                "data": row_data,
                "created_at": datetime.utcnow().isoformat(),
            })
        
        errors = self.bq_client.insert_rows_json(table_ref, rows)
        return len(errors) == 0
    
    def save_embeddings(self, document_id: str, embeddings_data: List[Dict[str, Any]]) -> bool:
        """Save embeddings to BigQuery"""
        table_ref = f"{self.project_id}.{self.dataset_id}.embeddings"
        
        rows = []
        for emb_data in embeddings_data:
            rows.append({
                "embedding_id": emb_data["embedding_id"],
                "document_id": document_id,
                "row_index": emb_data["row_index"],
                "chunk_text": emb_data["chunk_text"],
                "embedding": emb_data["embedding"],
                "metadata": emb_data.get("metadata", {}),
                "created_at": datetime.utcnow().isoformat(),
            })
        
        errors = self.bq_client.insert_rows_json(table_ref, rows)
        return len(errors) == 0
    
    def verify_embeddings(self, document_id: str) -> bool:
        """Verify that embeddings were created for a document"""
        try:
            query = f"""
            SELECT COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.embeddings`
            WHERE document_id = '{document_id}'
            """
            results = self.bq_client.query(query).result()
            count = list(results)[0]['count']
            return count > 0
        except Exception as e:
            print(f"Error verifying embeddings: {e}")
            return False
    
    def query_data(self, doc_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Query structured data from BigQuery"""
        query = f"""
        SELECT * FROM `{self.project_id}.{self.dataset_id}.structured_data`
        """
        if doc_type:
            query += f" WHERE doc_type = '{doc_type}'"
        query += f" LIMIT {limit}"
        
        results = self.bq_client.query(query).result()
        return [dict(row) for row in results]
    
    # Firestore operations
    def save_session(self, session_id: str, user_id: str, data: Dict[str, Any]) -> bool:
        """Save session data to Firestore"""
        try:
            doc_ref = self.firestore_client.collection('sessions').document(session_id)
            doc_ref.set({
                'user_id': user_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                **data
            }, merge=True)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Firestore"""
        try:
            doc_ref = self.firestore_client.collection('sessions').document(session_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    def save_chat_message(self, session_id: str, role: str, content: str) -> bool:
        """Save chat message to Firestore"""
        try:
            messages_ref = self.firestore_client.collection('sessions').document(session_id).collection('messages')
            messages_ref.add({
                'role': role,
                'content': content,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history from Firestore"""
        try:
            messages_ref = self.firestore_client.collection('sessions').document(session_id).collection('messages')
            messages = messages_ref.order_by('timestamp').limit(limit).stream()
            return [msg.to_dict() for msg in messages]
        except Exception as e:
            print(f"Error getting chat history: {e}")
            return []
    
    def save_checklist_status(self, user_id: str, checklist: Dict[str, str]) -> bool:
        """Save checklist status to Firestore"""
        try:
            doc_ref = self.firestore_client.collection('checklists').document(user_id)
            doc_ref.set({
                'checklist': checklist,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            return True
        except Exception as e:
            print(f"Error saving checklist: {e}")
            return False
    
    def get_checklist_status(self, user_id: str) -> Dict[str, str]:
        """Get checklist status from Firestore"""
        try:
            doc_ref = self.firestore_client.collection('checklists').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict().get('checklist', {})
            return {}
        except Exception as e:
            print(f"Error getting checklist: {e}")
            return {}


# Global instance
storage_service = StorageService()
