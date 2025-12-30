"""
Pydantic data models for OmniAgent.

These models define the structure of data flowing through the system:
- Dataset metadata
- Chat messages
- Tool calls and responses
- Analysis results
"""

from omniagent.models.dataset import ColumnInfo, DatasetMetadata, DatasetProfile
from omniagent.models.messages import ChatMessage, MessageRole, Conversation
from omniagent.models.tool_calls import ToolCall, ToolResult
from omniagent.models.results import (
    QueryResult,
    StatsSummary,
    CorrelationMatrix,
    RegressionResult,
    PlotResult,
)

__all__ = [
    # Dataset
    "ColumnInfo",
    "DatasetMetadata",
    "DatasetProfile",
    # Messages
    "ChatMessage",
    "MessageRole",
    "Conversation",
    # Tools
    "ToolCall",
    "ToolResult",
    # Results
    "QueryResult",
    "StatsSummary",
    "CorrelationMatrix",
    "RegressionResult",
    "PlotResult",
]
