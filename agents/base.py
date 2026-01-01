"""
Base Agent Module
=================
Abstract base class for all agents.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import pandas as pd

from core.analyzer import DataAnalyzer
from mcp.protocol import MCPMessage, AgentResponse


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    name: str = "Base Agent"
    emoji: str = "🤖"
    description: str = "Base agent"
    
    def __init__(self, df: pd.DataFrame, analyzer: DataAnalyzer):
        self.df = df
        self.analyzer = analyzer
    
    @abstractmethod
    def process(self, query: str) -> Dict[str, Any]:
        """Process a query and return response."""
        pass
    
    def process_message(self, message: MCPMessage) -> AgentResponse:
        """Process an MCP message."""
        result = self.process(message.content)
        return AgentResponse(
            content=result.get('content', ''),
            figure=result.get('figure'),
            dataframe=result.get('dataframe'),
            insights=result.get('insights'),
            suggestions=result.get('suggestions', []),
            agent_name=self.name,
            agent_emoji=self.emoji,
            success=True
        )
    
    def find_column(self, name: str) -> Optional[str]:
        """Find column by name using analyzer."""
        return self.analyzer.find_column(name)
    
    def get_suggestions(self) -> List[str]:
        """Get default suggestions for this agent."""
        return []
    
    def format_error(self, message: str) -> Dict[str, Any]:
        """Format an error response."""
        return {
            'content': f"## {self.emoji} {self.name}\n\n❌ {message}",
            'insights': None,
            'suggestions': self.get_suggestions()
        }
