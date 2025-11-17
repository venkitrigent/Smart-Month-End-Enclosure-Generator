"""
Embedding service for generating and managing embeddings
Uses Vertex AI Text Embeddings (Google Cloud native)
"""

import os
from typing import List, Dict, Any
import uuid
from vertexai.language_models import TextEmbeddingModel


class EmbeddingService:
    """Handles embedding generation for RAG using Vertex AI"""
    
    def __init__(self):
        # Use Vertex AI text embedding model (Google Cloud native)
        # Available models:
        # - textembedding-gecko@003 (768 dimensions, multilingual)
        # - textembedding-gecko@002 (768 dimensions)
        # - textembedding-gecko@001 (768 dimensions)
        self.model_name = os.getenv('VERTEX_EMBEDDING_MODEL', 'textembedding-gecko@003')
        self.model = None
        self.embedding_dimension = 768  # Gecko models use 768 dimensions
        self._load_model()
    
    def _load_model(self):
        """Lazy load the Vertex AI embedding model"""
        try:
            self.model = TextEmbeddingModel.from_pretrained(self.model_name)
            print(f"✅ Loaded Vertex AI embedding model: {self.model_name}")
        except Exception as e:
            print(f"⚠️ Error loading Vertex AI embedding model: {e}")
            print("Falling back to zero embeddings")
            self.model = None
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using Vertex AI
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (768 dimensions each)
        """
        if not self.model:
            self._load_model()
        
        if not self.model:
            # Return zero embeddings if model failed to load
            print("⚠️ Model not available, returning zero embeddings")
            return [[0.0] * self.embedding_dimension for _ in texts]
        
        try:
            # Vertex AI supports batch embedding
            # Split into batches of 5 (API limit)
            batch_size = 5
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self.model.get_embeddings(batch)
                all_embeddings.extend([emb.values for emb in embeddings])
            
            return all_embeddings
        except Exception as e:
            print(f"⚠️ Error generating embeddings: {e}")
            # Return zero embeddings as fallback
            return [[0.0] * self.embedding_dimension for _ in texts]
    
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
