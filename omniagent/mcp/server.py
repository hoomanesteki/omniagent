"""
MCP Server base class for agents.

Provides:
- Tool registration decorator
- Request handling
- Response formatting
"""

import time
from functools import wraps
from typing import Any, Callable, TypeVar

from omniagent.config.logging import AgentLogger, get_logger
from omniagent.mcp.protocol import MCPError, MCPRequest, MCPResponse
from omniagent.mcp.registry import ToolRegistry, get_registry

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def mcp_tool(func: F) -> F:
    """
    Decorator to mark a method as an MCP tool.
    
    Usage:
        class MyAgent(MCPServer):
            @mcp_tool
            def my_tool(self, param: str) -> dict:
                '''Tool description.'''
                return {"result": "..."}
    
    The decorator:
    - Marks the method for registration
    - Adds timing and logging
    - Wraps errors properly
    """
    func._is_mcp_tool = True  # type: ignore
    return func


class MCPServer:
    """
    Base class for MCP agent servers.
    
    Subclasses should:
    1. Define `name` and `description` class attributes
    2. Implement tools using the @mcp_tool decorator
    3. Call super().__init__() to register tools
    
    Example:
        class SQLAgent(MCPServer):
            name = "sql_agent"
            description = "Executes safe SQL queries"
            
            @mcp_tool
            def query(self, sql: str) -> dict:
                '''Execute a SELECT query.'''
                # Implementation
                return {"rows": [...]}
    """
    
    name: str = "base_agent"
    description: str = "Base MCP agent"
    
    def __init__(self, registry: ToolRegistry | None = None):
        """
        Initialize the MCP server.
        
        Args:
            registry: Tool registry to use. Uses global if not provided.
        """
        self.registry = registry or get_registry()
        self.logger = AgentLogger(self.name)
        self._tools: dict[str, Callable[..., Any]] = {}
        
        # Auto-register all @mcp_tool decorated methods
        self._register_tools()
    
    def _register_tools(self) -> None:
        """Find and register all @mcp_tool decorated methods."""
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            
            attr = getattr(self, attr_name)
            if callable(attr) and getattr(attr, "_is_mcp_tool", False):
                # Register with the registry
                self.registry.register(
                    agent_name=self.name,
                    tool_name=attr_name,
                    handler=attr,
                )
                self._tools[attr_name] = attr
                logger.debug(f"Registered tool: {self.name}.{attr_name}")
    
    def get_tools(self) -> list[str]:
        """Get list of tool names provided by this agent."""
        return list(self._tools.keys())
    
    def handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        Handle an incoming MCP request.
        
        Args:
            request: The MCP request to handle
            
        Returns:
            MCPResponse with result or error
        """
        # Parse method name (could be "tool_name" or "agent.tool_name")
        method = request.method
        if "." in method:
            agent_name, tool_name = method.rsplit(".", 1)
            if agent_name != self.name:
                return MCPResponse.error_response(
                    request.id,
                    MCPError.method_not_found(method),
                )
        else:
            tool_name = method
        
        # Find the tool
        handler = self._tools.get(tool_name)
        if handler is None:
            return MCPResponse.error_response(
                request.id,
                MCPError.method_not_found(f"{self.name}.{tool_name}"),
            )
        
        # Log the call
        self.logger.tool_call(tool_name, request.params)
        
        # Execute the tool
        start_time = time.perf_counter()
        try:
            result = handler(**request.params)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            self.logger.tool_result(
                tool_name,
                success=True,
                duration_ms=duration_ms,
            )
            
            return MCPResponse.success(request.id, result)
            
        except TypeError as e:
            # Parameter errors
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.tool_error(tool_name, e)
            
            return MCPResponse.error_response(
                request.id,
                MCPError.invalid_params(str(e)),
            )
            
        except Exception as e:
            # Tool execution errors
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.tool_error(tool_name, e)
            
            return MCPResponse.error_response(
                request.id,
                MCPError.tool_error(str(e)),
            )
    
    async def handle_request_async(self, request: MCPRequest) -> MCPResponse:
        """
        Async version of handle_request.
        
        For agents with async tool implementations.
        """
        # For now, just wrap the sync version
        # Subclasses can override for true async
        return self.handle_request(request)
