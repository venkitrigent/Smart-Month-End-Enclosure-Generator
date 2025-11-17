"""
Embedding service for generating and managing embeddings
"""

import os
from typing import List, Dict, Any
import uuid
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Handles embedding generation for RAG"""
    
    def __init__(self):
        # Use a lightweight model for fast inference
        self.model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Lazy load the embedding model"""
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            self.model = None
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not self.model:
            self._load_model()
        
        if not self.model:
            # Return empty embeddings if model failed to load
            return [[0.0] * 384 for _ in texts]
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return [[0.0] * 384 for _ in texts]
    
    def create_chunks_with_embeddings(self, document_id: str, rows: List[Dict[str, Any]], 
                                     columns: List[str]) -> List[Dict[str, Any]]:
        """Create text chunks and generate embeddings"""
        chunks = []
        texts = []
        
        # Create column-aware chunks
        for idx, row in enumerate(rows):
            chunk_text = ", ".join([f"{col}: {row.get(col, 'N/A')}" for col in columns])
            chunks.append({
                "embedding_id": f"{document_id}_{idx}",
                "row_index": idx,
                "chunk_text": chunk_text,
                "metadata": {
                    "document_id": document_id,
                    "columns": columns
                }
            })
            texts.append(chunk_text)
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
        
        return chunks
    
    def search_similar(self, query: str, embeddings_data: List[Dict[str, Any]], 
                      top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks using cosine similarity"""
        if not embeddings_data:
            return []
        
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        # Calculate cosine similarity
        similarities = []
        for item in embeddings_data:
            embedding = item.get("embedding", [])
            if not embedding:
                continue
            
            # Cosine similarity
            dot_product = sum(a * b for a, b in zip(query_embedding, embedding))
            norm_a = sum(a * a for a in query_embedding) ** 0.5
            norm_b = sum(b * b for b in embedding) ** 0.5
            
            if norm_a > 0 and norm_b > 0:
                similarity = dot_product / (norm_a * norm_b)
                similarities.append({
                    **item,
                    "similarity": similarity
                })
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]


# Global instance
embedding_service = EmbeddingService()
