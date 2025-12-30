"""
MCP Client for the Master Agent.

Provides:
- Tool invocation across agents
- Response handling
- Agent management
"""

import time
from typing import Any

from omniagent.config.logging import get_logger
from omniagent.mcp.protocol import MCPRequest, MCPResponse, ToolCallMessage, ToolResultMessage
from omniagent.mcp.registry import ToolRegistry, get_registry
from omniagent.mcp.server import MCPServer

logger = get_logger(__name__)


class MCPClient:
    """
    MCP Client for invoking tools on agent servers.
    
    The Master Agent uses this to call tools on specialized agents.
    
    Example:
        client = MCPClient()
        client.register_agent(sql_agent)
        client.register_agent(stats_agent)
        
        result = client.call_tool("sql_agent.query", {"sql": "SELECT * FROM data"})
    """
    
    def __init__(self, registry: ToolRegistry | None = None):
        """
        Initialize the MCP client.
        
        Args:
            registry: Tool registry to use. Uses global if not provided.
        """
        self.registry = registry or get_registry()
        self._agents: dict[str, MCPServer] = {}
        self._request_counter = 0
    
    def register_agent(self, agent: MCPServer) -> None:
        """
        Register an agent with the client.
        
        Args:
            agent: The agent server to register
        """
        self._agents[agent.name] = agent
        logger.info(f"Agent registered: {agent.name} with {len(agent.get_tools())} tools")
    
    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent.
        
        Returns True if agent was found and removed.
        """
        if agent_name in self._agents:
            del self._agents[agent_name]
            return True
        return False
    
    def get_agent(self, agent_name: str) -> MCPServer | None:
        """Get an agent by name."""
        return self._agents.get(agent_name)
    
    def list_agents(self) -> list[str]:
        """Get list of registered agent names."""
        return list(self._agents.keys())
    
    def _next_request_id(self) -> str:
        """Generate unique request ID."""
        self._request_counter += 1
        return f"req_{self._request_counter}_{int(time.time() * 1000)}"
    
    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        request_id: str | None = None,
    ) -> MCPResponse:
        """
        Call a tool on an agent.
        
        Args:
            tool_name: Full tool name (e.g., "sql_agent.query")
            arguments: Tool arguments
            request_id: Optional request ID (auto-generated if not provided)
            
        Returns:
            MCPResponse with result or error
        """
        # Parse agent and tool name
        if "." in tool_name:
            agent_name, method_name = tool_name.split(".", 1)
        else:
            # Try to find which agent has this tool
            agent_name = None
            method_name = tool_name
            for name, agent in self._agents.items():
                if tool_name in agent.get_tools():
                    agent_name = name
                    break
            
            if agent_name is None:
                from omniagent.mcp.protocol import MCPError
                return MCPResponse.error_response(
                    request_id or self._next_request_id(),
                    MCPError.method_not_found(tool_name),
                )
        
        # Get the agent
        agent = self._agents.get(agent_name)
        if agent is None:
            from omniagent.mcp.protocol import MCPError
            return MCPResponse.error_response(
                request_id or self._next_request_id(),
                MCPError.method_not_found(f"Agent not found: {agent_name}"),
            )
        
        # Create request
        request = MCPRequest(
            id=request_id or self._next_request_id(),
            method=f"{agent_name}.{method_name}",
            params=arguments,
        )
        
        # Execute
        logger.debug(f"Calling tool: {tool_name}", arguments=arguments)
        response = agent.handle_request(request)
        
        if response.is_error:
            logger.warning(f"Tool error: {tool_name}", error=response.error)
        else:
            logger.debug(f"Tool success: {tool_name}")
        
        return response
    
    def call_tool_from_llm(
        self,
        tool_call: ToolCallMessage,
    ) -> ToolResultMessage:
        """
        Call a tool from an LLM tool call message.
        
        This is the main method used by the Master Agent when
        processing Claude's tool calls.
        
        Args:
            tool_call: Tool call from the LLM
            
        Returns:
            ToolResultMessage to send back to the LLM
        """
        response = self.call_tool(
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
            request_id=tool_call.id,
        )
        
        return ToolResultMessage.from_mcp_response(
            tool_call_id=tool_call.id,
            response=response,
        )
    
    def get_available_tools(
        self,
        agent_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get tool schemas for the LLM.
        
        Args:
            agent_names: Filter to specific agents. None for all.
            
        Returns:
            List of tool schemas in Anthropic format
        """
        return self.registry.get_anthropic_schemas(agent_names)
    
    def get_tool_descriptions(self) -> str:
        """
        Get a human-readable description of all available tools.
        
        Useful for including in system prompts.
        """
        lines = ["Available tools:"]
        
        for agent_name in sorted(self._agents.keys()):
            tools = self.registry.get_agent_tools(agent_name)
            lines.append(f"\n## {agent_name}")
            
            for tool in tools:
                lines.append(f"- **{tool.name}**: {tool.description}")
                if tool.parameters:
                    params = ", ".join(
                        f"{p.name}: {p.type}"
                        for p in tool.parameters
                    )
                    lines.append(f"  Parameters: {params}")
        
        return "\n".join(lines)
