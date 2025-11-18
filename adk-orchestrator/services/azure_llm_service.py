"""
Azure OpenAI Service for LLM calls
Provides direct Azure OpenAI integration for classification, analysis, and chat.
Note: ADK agents use LiteLLM which handles Azure OpenAI automatically via environment variables.
"""
import os
from typing import List, Dict
from openai import AzureOpenAI

class AzureLLMService:
    """Service for Azure OpenAI integration (for non-ADK direct calls)"""
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        # Check if Azure OpenAI is configured
        if not os.getenv("AZURE_OPENAI_API_KEY"):
            print("⚠️ Azure OpenAI not configured. Set AZURE_OPENAI_API_KEY in .env")
            self.client = None
            return
        
        try:
            self.client = AzureOpenAI(
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
            )
            self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
            self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
            print(f"✅ Azure OpenAI initialized: {self.deployment_name}")
        except Exception as e:
            print(f"❌ Failed to initialize Azure OpenAI: {e}")
            self.client = None
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate chat completion using Azure OpenAI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        if not self.client:
            return "Azure OpenAI not configured. Please set AZURE_OPENAI_API_KEY."
        
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ Azure OpenAI error: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_response(
        self, 
        prompt: str, 
        system_message: str = None,
        temperature: float = 0.7
    ) -> str:
        """
        Simple prompt-based generation
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat_completion(messages, temperature=temperature)
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings using Azure OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding error: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * 1536
    
    def analyze_financial_data(self, data: str, doc_type: str) -> Dict:
        """
        Analyze financial data using Azure OpenAI
        
        Args:
            data: Financial data as string
            doc_type: Type of document
            
        Returns:
            Analysis results
        """
        system_message = """You are a financial analyst expert specializing in month-end close processes.
        Analyze the provided financial data and provide actionable insights."""
        
        prompt = f"""Analyze this {doc_type} data:

{data[:2000]}  # Limit data size

Provide:
1. Key financial insights
2. Any anomalies or concerns
3. Recommendations for month-end close
4. Data quality assessment

Format your response as JSON with keys: insights, anomalies, recommendations, quality_score"""
        
        response = self.generate_response(prompt, system_message, temperature=0.3)
        
        return {
            "analysis": response,
            "model": "azure-openai",
            "deployment": self.deployment_name
        }
    
    def classify_document(self, filename: str, sample_data: str = None) -> Dict:
        """
        Classify document type using Azure OpenAI
        
        Args:
            filename: Name of the file
            sample_data: Optional sample of file content
            
        Returns:
            Classification result
        """
        system_message = """You are a document classification expert for financial documents.
        Classify the document into one of these types:
        - bank_statement
        - invoice_register
        - general_ledger
        - trial_balance
        - reconciliation_report
        - other"""
        
        prompt = f"""Classify this document:
Filename: {filename}
Sample data: {sample_data[:500] if sample_data else 'N/A'}

Return ONLY the document type from the list above."""
        
        doc_type = self.generate_response(prompt, system_message, temperature=0.1).strip().lower()
        
        # Validate response
        valid_types = ["bank_statement", "invoice_register", "general_ledger", 
                      "trial_balance", "reconciliation_report", "other"]
        
        if doc_type not in valid_types:
            doc_type = "other"
        
        return {
            "doc_type": doc_type,
            "confidence": 0.85,
            "model": "azure-openai"
        }
    
    def generate_report_summary(self, report_data: Dict) -> str:
        """
        Generate natural language summary of month-end report
        
        Args:
            report_data: Report data dictionary
            
        Returns:
            Natural language summary
        """
        system_message = """You are a financial reporting expert.
        Create a concise executive summary of the month-end close report."""
        
        prompt = f"""Create an executive summary for this month-end close report:

Total Documents: {report_data.get('total_documents', 0)}
Total Rows: {report_data.get('total_rows', 0)}
Completion: {report_data.get('completion_percentage', '0%')}
Status: {report_data.get('status', 'Unknown')}

Documents by Type: {report_data.get('documents_by_type', {})}

Provide a 3-4 sentence executive summary highlighting key points and any concerns."""
        
        return self.generate_response(prompt, system_message, temperature=0.5)
    
    def chat_with_context(self, query: str, context: str, history: str = "") -> Dict:
        """
        Chat with RAG context from uploaded documents
        
        Args:
            query: User's question
            context: Retrieved context from embeddings
            history: Conversation history
            
        Returns:
            Response dictionary
        """
        system_message = """You are a helpful financial assistant for month-end close processes.
        Answer questions based on the provided context from uploaded financial documents.
        
        Guidelines:
        - Always reference specific data from the context
        - Be precise with numbers and financial information
        - If the context doesn't contain the answer, say so clearly
        - Provide actionable insights when possible
        - Keep responses concise but informative"""
        
        prompt = f"""Context from uploaded documents:
{context}

Previous conversation:
{history}

User question: {query}

Provide a helpful, accurate answer based on the context above."""
        
        response = self.generate_response(prompt, system_message, temperature=0.3)
        
        return {
            "response": response,
            "model": "azure-openai",
            "deployment": self.deployment_name
        }

# Global instance
azure_llm = AzureLLMService()
