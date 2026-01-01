"""
LLM Client Module
=================
Groq API client for AI-enhanced responses.
"""

import os
from typing import List, Dict, Optional

try:
    import requests
except ImportError:
    requests = None


class LLMClient:
    """LLM client for AI-enhanced responses."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.available = bool(self.api_key)
        self.enabled = True
        self.max_tokens = 2000
        self.temperature = 0.1
        self.timeout = 30
    
    def set_api_key(self, key: str):
        """Set API key dynamically."""
        self.api_key = key
        self.available = bool(key)
    
    def toggle(self, enabled: bool):
        """Enable/disable LLM."""
        self.enabled = enabled
    
    def is_active(self) -> bool:
        """Check if LLM is both available and enabled."""
        return self.available and self.enabled and requests is not None
    
    def chat(self, messages: List[Dict], temperature: float = None) -> Optional[str]:
        """Send chat completion request to Groq API."""
        if not self.is_active():
            return None
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature or self.temperature,
                    "max_tokens": self.max_tokens
                },
                timeout=self.timeout
            )
            
            if response.status_code == 429:
                return None  # Rate limited
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception:
            return None
    
    def enhance_response(self, query: str, context: str, base_response: str) -> str:
        """Use LLM to enhance a response with more detail."""
        if not self.is_active():
            return base_response
        
        prompt = f"""You are a helpful data analysis assistant. The user asked: "{query}"

Context about the data:
{context}

Base response to enhance:
{base_response}

Please provide a more detailed, friendly, and insightful response. Be specific about what the data shows.
Keep it concise but informative. Use bullet points for key insights."""
        
        result = self.chat([{"role": "user", "content": prompt}])
        return result if result else base_response
    
    def understand_query(self, query: str, context: str) -> Optional[str]:
        """Use LLM to understand ambiguous queries."""
        if not self.is_active():
            return None
        
        prompt = f"""User asked: "{query}"
Context: {context}

Determine what the user wants. Respond with a helpful answer about the data.
If they want a summary/overview, describe the dataset comprehensively.
Be specific, friendly, and informative."""
        
        return self.chat([{"role": "user", "content": prompt}])
