"""
MCP (Model Context Protocol) implementation for OmniAgent.

This module provides:
- MCP server base class for agents
- MCP client for the Master Agent
- JSON-RPC protocol handling
- Tool registration and discovery
"""

from omniagent.mcp.server import MCPServer, mcp_tool
from omniagent.mcp.client import MCPClient
from omniagent.mcp.protocol import MCPRequest, MCPResponse, MCPError
from omniagent.mcp.registry import ToolRegistry, ToolDefinition

__all__ = [
    "MCPServer",
    "mcp_tool",
    "MCPClient",
    "MCPRequest",
    "MCPResponse",
    "MCPError",
    "ToolRegistry",
    "ToolDefinition",
]
