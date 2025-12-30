"""
MCP Protocol message definitions.

Implements JSON-RPC 2.0 based messaging for MCP communication.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MCPErrorCode(int, Enum):
    """Standard JSON-RPC error codes."""
    
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Custom MCP error codes
    TOOL_EXECUTION_ERROR = -32000
    VALIDATION_ERROR = -32001
    TIMEOUT_ERROR = -32002


class MCPError(BaseModel):
    """JSON-RPC error object."""
    
    code: int = Field(description="Error code")
    message: str = Field(description="Error message")
    data: Any = Field(default=None, description="Additional error data")
    
    @classmethod
    def method_not_found(cls, method: str) -> "MCPError":
        return cls(
            code=MCPErrorCode.METHOD_NOT_FOUND,
            message=f"Method not found: {method}",
        )
    
    @classmethod
    def invalid_params(cls, message: str) -> "MCPError":
        return cls(
            code=MCPErrorCode.INVALID_PARAMS,
            message=message,
        )
    
    @classmethod
    def tool_error(cls, message: str, data: Any = None) -> "MCPError":
        return cls(
            code=MCPErrorCode.TOOL_EXECUTION_ERROR,
            message=message,
            data=data,
        )
    
    @classmethod
    def internal_error(cls, message: str) -> "MCPError":
        return cls(
            code=MCPErrorCode.INTERNAL_ERROR,
            message=message,
        )


class MCPRequest(BaseModel):
    """
    MCP JSON-RPC request message.
    
    Used to call tools on agent servers.
    """
    
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: str | int = Field(description="Request ID")
    method: str = Field(description="Method/tool to call")
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="Method parameters",
    )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
            "method": self.method,
            "params": self.params,
        }


class MCPResponse(BaseModel):
    """
    MCP JSON-RPC response message.
    
    Returned from tool executions.
    """
    
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: str | int = Field(description="Request ID this responds to")
    result: Any = Field(default=None, description="Result data (on success)")
    error: MCPError | None = Field(default=None, description="Error (on failure)")
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.error is None
    
    @property
    def is_error(self) -> bool:
        """Check if response indicates error."""
        return self.error is not None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data: dict[str, Any] = {
            "jsonrpc": self.jsonrpc,
            "id": self.id,
        }
        if self.error:
            data["error"] = self.error.model_dump()
        else:
            data["result"] = self.result
        return data
    
    @classmethod
    def success(cls, request_id: str | int, result: Any) -> "MCPResponse":
        """Create a success response."""
        return cls(id=request_id, result=result)
    
    @classmethod
    def error_response(
        cls,
        request_id: str | int,
        error: MCPError,
    ) -> "MCPResponse":
        """Create an error response."""
        return cls(id=request_id, error=error)


class MCPNotification(BaseModel):
    """
    MCP notification message (no response expected).
    
    Used for events like progress updates.
    """
    
    jsonrpc: str = Field(default="2.0")
    method: str = Field(description="Notification method")
    params: dict[str, Any] = Field(default_factory=dict)
    
    # No id field - notifications don't expect responses


class ToolCallMessage(BaseModel):
    """
    Represents a tool call from the LLM.
    
    This is the format Claude/OpenAI use for tool calls.
    """
    
    id: str = Field(description="Tool call ID")
    name: str = Field(description="Tool name")
    arguments: dict[str, Any] = Field(description="Tool arguments")
    
    def to_mcp_request(self) -> MCPRequest:
        """Convert to MCP request format."""
        return MCPRequest(
            id=self.id,
            method=self.name,
            params=self.arguments,
        )


class ToolResultMessage(BaseModel):
    """
    Represents a tool result to send back to the LLM.
    """
    
    tool_call_id: str = Field(description="ID of the tool call")
    content: str = Field(description="Result content (usually JSON string)")
    is_error: bool = Field(default=False, description="Whether this is an error")
    
    @classmethod
    def from_mcp_response(
        cls,
        tool_call_id: str,
        response: MCPResponse,
    ) -> "ToolResultMessage":
        """Create from MCP response."""
        import json
        
        if response.is_error:
            return cls(
                tool_call_id=tool_call_id,
                content=response.error.message if response.error else "Unknown error",
                is_error=True,
            )
        else:
            content = json.dumps(response.result, default=str)
            return cls(
                tool_call_id=tool_call_id,
                content=content,
                is_error=False,
            )
