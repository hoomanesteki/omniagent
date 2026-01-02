"""
LLM Client Module
=================
Groq API client for AI-enhanced responses and dynamic code generation.
"""

import os
from typing import List, Dict, Optional, Any

try:
    import requests
except ImportError:
    requests = None


class LLMClient:
    """LLM client for AI-enhanced responses and code generation."""
    
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
    
    def chat(self, messages: List[Dict], temperature: float = None, max_tokens: int = None) -> Optional[str]:
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
                    "max_tokens": max_tokens or self.max_tokens
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
    
    def generate_analysis_code(self, query: str, df_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate Python code to answer a data analysis question.
        Returns dict with: plan, code, explanation
        """
        if not self.is_active():
            return None
        
        # Build context about the dataframe
        columns_info = "\n".join([
            f"  - {col}: {dtype}" for col, dtype in df_info.get('dtypes', {}).items()
        ])
        
        prompt = f"""You are an expert data analyst. Generate Python code to answer this question:

QUESTION: "{query}"

DATAFRAME INFO:
- Shape: {df_info.get('shape', 'Unknown')}
- Columns and types:
{columns_info}

SAMPLE DATA (first 3 rows):
{df_info.get('sample', 'Not available')}

NUMERIC COLUMNS: {df_info.get('numeric_cols', [])}
CATEGORICAL COLUMNS: {df_info.get('categorical_cols', [])}

INSTRUCTIONS:
1. The dataframe is available as `df` (pandas DataFrame)
2. Available libraries: pandas (pd), numpy (np), plotly.express (px), plotly.graph_objects (go), sklearn
3. Your code should create a variable called `result` with the answer
4. For visualizations, create a variable called `fig` (plotly figure)
5. For dataframes, create a variable called `result_df`
6. Keep code simple and safe - no file operations, no network calls
7. Handle missing values appropriately

Respond in this EXACT format:
PLAN: [Brief explanation of what you'll do]
CODE:
```python
[your code here]
```
EXPLANATION: [What the result shows]"""

        response = self.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2500
        )
        
        if not response:
            return None
        
        # Parse the response
        try:
            result = {
                'plan': '',
                'code': '',
                'explanation': ''
            }
            
            # Extract plan
            if 'PLAN:' in response:
                plan_start = response.find('PLAN:') + 5
                plan_end = response.find('CODE:') if 'CODE:' in response else len(response)
                result['plan'] = response[plan_start:plan_end].strip()
            
            # Extract code
            if '```python' in response:
                code_start = response.find('```python') + 9
                code_end = response.find('```', code_start)
                if code_end > code_start:
                    result['code'] = response[code_start:code_end].strip()
            elif '```' in response:
                code_start = response.find('```') + 3
                code_end = response.find('```', code_start)
                if code_end > code_start:
                    result['code'] = response[code_start:code_end].strip()
            
            # Extract explanation
            if 'EXPLANATION:' in response:
                exp_start = response.find('EXPLANATION:') + 12
                result['explanation'] = response[exp_start:].strip()
            
            return result if result['code'] else None
            
        except Exception:
            return None
    
    def analyze_error(self, code: str, error: str, query: str) -> Optional[str]:
        """Analyze an error and suggest a fix."""
        if not self.is_active():
            return None
        
        prompt = f"""The following Python code produced an error:

CODE:
```python
{code}
```

ERROR: {error}

ORIGINAL QUESTION: {query}

Please provide a brief explanation of what went wrong and suggest how to fix it.
Keep the response short and actionable."""
        
        return self.chat([{"role": "user", "content": prompt}], temperature=0.1)
