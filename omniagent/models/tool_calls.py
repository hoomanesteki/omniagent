"""
Tool call data models.

These models represent requests to and responses from
MCP tool servers.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ToolStatus(str, Enum):
    """Status of a tool execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class ToolCall(BaseModel):
    """A request to execute a tool."""
    
    id: str = Field(description="Unique ID for this tool call")
    agent_name: str = Field(description="Target agent (e.g., 'sql_agent')")
    tool_name: str = Field(description="Tool to execute (e.g., 'query')")
    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool arguments",
    )
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    
    def to_mcp_request(self) -> dict[str, Any]:
        """Convert to MCP JSON-RPC request format."""
        return {
            "jsonrpc": "2.0",
            "id": self.id,
            "method": f"tools/{self.tool_name}",
            "params": self.arguments,
        }


class ToolResult(BaseModel):
    """Result from a tool execution."""
    
    tool_call_id: str = Field(description="ID of the original tool call")
    status: ToolStatus = Field(description="Execution status")
    
    # Result data (on success)
    data: Any = Field(default=None, description="Result data")
    
    # Error info (on failure)
    error_message: str | None = Field(default=None, description="Error message")
    error_type: str | None = Field(default=None, description="Error type")
    
    # Timing
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    duration_ms: float | None = Field(default=None, description="Execution time in ms")
    
    @property
    def is_success(self) -> bool:
        """Check if tool execution was successful."""
        return self.status == ToolStatus.SUCCESS
    
    @property
    def is_error(self) -> bool:
        """Check if tool execution failed."""
        return self.status == ToolStatus.ERROR
    
    def to_string_for_llm(self) -> str:
        """Format result for including in LLM context."""
        if self.is_success:
            if isinstance(self.data, dict):
                # Format dict nicely
                import json
                return json.dumps(self.data, indent=2, default=str)
            return str(self.data)
        else:
            return f"Error: {self.error_message}"
    
    @classmethod
    def success(
        cls,
        tool_call_id: str,
        data: Any,
        duration_ms: float | None = None,
    ) -> "ToolResult":
        """Create a successful result."""
        return cls(
            tool_call_id=tool_call_id,
            status=ToolStatus.SUCCESS,
            data=data,
            duration_ms=duration_ms,
            completed_at=datetime.now(),
        )
    
    @classmethod
    def error(
        cls,
        tool_call_id: str,
        error: Exception,
        duration_ms: float | None = None,
    ) -> "ToolResult":
        """Create an error result."""
        return cls(
            tool_call_id=tool_call_id,
            status=ToolStatus.ERROR,
            error_message=str(error),
            error_type=type(error).__name__,
            duration_ms=duration_ms,
            completed_at=datetime.now(),
        )
