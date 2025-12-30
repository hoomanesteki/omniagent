"""
Tool registry for MCP agents.

Handles:
- Tool registration
- Tool discovery
- Schema generation for LLM
"""

import inspect
from typing import Any, Callable, get_type_hints

from pydantic import BaseModel, Field

from omniagent.config.logging import get_logger

logger = get_logger(__name__)


class ToolParameter(BaseModel):
    """Definition of a tool parameter."""
    
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type")
    description: str = Field(default="", description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Any = Field(default=None, description="Default value if not required")


class ToolDefinition(BaseModel):
    """
    Complete definition of a tool.
    
    Used for tool discovery and LLM schema generation.
    """
    
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    agent_name: str = Field(description="Agent that owns this tool")
    parameters: list[ToolParameter] = Field(
        default_factory=list,
        description="Tool parameters",
    )
    
    def to_anthropic_schema(self) -> dict[str, Any]:
        """
        Convert to Anthropic tool schema format.
        
        This is what Claude expects for tool definitions.
        """
        properties = {}
        required = []
        
        for param in self.parameters:
            # Map Python types to JSON Schema types
            type_map = {
                "str": "string",
                "int": "integer",
                "float": "number",
                "bool": "boolean",
                "list": "array",
                "dict": "object",
            }
            
            json_type = type_map.get(param.type, "string")
            
            properties[param.name] = {
                "type": json_type,
                "description": param.description,
            }
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
    
    def to_openai_schema(self) -> dict[str, Any]:
        """
        Convert to OpenAI tool schema format.
        """
        anthropic_schema = self.to_anthropic_schema()
        return {
            "type": "function",
            "function": {
                "name": anthropic_schema["name"],
                "description": anthropic_schema["description"],
                "parameters": anthropic_schema["input_schema"],
            },
        }


class ToolRegistry:
    """
    Central registry for all tools across agents.
    
    Provides:
    - Tool registration
    - Tool lookup
    - Schema generation for LLMs
    """
    
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._agents: dict[str, list[str]] = {}  # agent_name -> tool_names
    
    def register(
        self,
        agent_name: str,
        tool_name: str,
        handler: Callable[..., Any],
        description: str | None = None,
    ) -> ToolDefinition:
        """
        Register a tool.
        
        Args:
            agent_name: Name of the agent owning this tool
            tool_name: Name of the tool
            handler: Function that implements the tool
            description: Tool description (extracted from docstring if not provided)
            
        Returns:
            ToolDefinition for the registered tool
        """
        # Extract description from docstring if not provided
        if description is None:
            description = inspect.getdoc(handler) or f"Tool: {tool_name}"
            # Get just the first line/paragraph
            description = description.split("\n\n")[0].strip()
        
        # Extract parameters from function signature
        parameters = self._extract_parameters(handler)
        
        # Create definition
        full_name = f"{agent_name}.{tool_name}"
        definition = ToolDefinition(
            name=full_name,
            description=description,
            agent_name=agent_name,
            parameters=parameters,
        )
        
        # Store
        self._tools[full_name] = definition
        self._handlers[full_name] = handler
        
        # Track by agent
        if agent_name not in self._agents:
            self._agents[agent_name] = []
        self._agents[agent_name].append(full_name)
        
        logger.debug(
            "Tool registered",
            tool=full_name,
            params=len(parameters),
        )
        
        return definition
    
    def _extract_parameters(
        self,
        handler: Callable[..., Any],
    ) -> list[ToolParameter]:
        """Extract parameters from function signature."""
        parameters = []
        sig = inspect.signature(handler)
        hints = get_type_hints(handler) if hasattr(handler, "__annotations__") else {}
        
        # Get docstring for parameter descriptions
        docstring = inspect.getdoc(handler) or ""
        param_docs = self._parse_param_docs(docstring)
        
        for name, param in sig.parameters.items():
            # Skip self parameter
            if name == "self":
                continue
            
            # Get type
            type_hint = hints.get(name, Any)
            type_name = getattr(type_hint, "__name__", str(type_hint))
            
            # Check if required
            required = param.default == inspect.Parameter.empty
            default = None if required else param.default
            
            # Get description from docstring
            description = param_docs.get(name, "")
            
            parameters.append(ToolParameter(
                name=name,
                type=type_name,
                description=description,
                required=required,
                default=default,
            ))
        
        return parameters
    
    def _parse_param_docs(self, docstring: str) -> dict[str, str]:
        """Parse parameter descriptions from docstring."""
        param_docs = {}
        
        # Look for Args: section
        if "Args:" in docstring:
            args_section = docstring.split("Args:")[1]
            if "Returns:" in args_section:
                args_section = args_section.split("Returns:")[0]
            
            # Parse each parameter line
            lines = args_section.strip().split("\n")
            current_param = None
            current_desc = []
            
            for line in lines:
                line = line.strip()
                if ":" in line and not line.startswith(" "):
                    # Save previous param
                    if current_param:
                        param_docs[current_param] = " ".join(current_desc).strip()
                    
                    # Parse new param
                    parts = line.split(":", 1)
                    current_param = parts[0].strip()
                    current_desc = [parts[1].strip()] if len(parts) > 1 else []
                elif current_param and line:
                    current_desc.append(line)
            
            # Save last param
            if current_param:
                param_docs[current_param] = " ".join(current_desc).strip()
        
        return param_docs
    
    def get_tool(self, full_name: str) -> ToolDefinition | None:
        """Get a tool definition by full name."""
        return self._tools.get(full_name)
    
    def get_handler(self, full_name: str) -> Callable[..., Any] | None:
        """Get a tool handler by full name."""
        return self._handlers.get(full_name)
    
    def get_agent_tools(self, agent_name: str) -> list[ToolDefinition]:
        """Get all tools for an agent."""
        tool_names = self._agents.get(agent_name, [])
        return [self._tools[name] for name in tool_names]
    
    def get_all_tools(self) -> list[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_anthropic_schemas(
        self,
        agent_names: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get tool schemas in Anthropic format.
        
        Args:
            agent_names: Filter to specific agents. None for all.
            
        Returns:
            List of tool schemas for Claude API
        """
        if agent_names is None:
            tools = self.get_all_tools()
        else:
            tools = []
            for agent in agent_names:
                tools.extend(self.get_agent_tools(agent))
        
        return [tool.to_anthropic_schema() for tool in tools]
    
    def list_agents(self) -> list[str]:
        """Get list of all registered agents."""
        return list(self._agents.keys())


# Global registry instance
_global_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _global_registry
