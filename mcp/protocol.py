"""
MCP Protocol Module
===================
Message Communication Protocol for agent communication.
Best-in-class implementation for multi-agent orchestration.

Features:
- Typed messages with routing
- Agent registry with capabilities
- Message history and tracing
- Error handling and recovery
- Response standardization
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of MCP messages."""
    QUERY = "query"           # User query to agent
    RESPONSE = "response"     # Agent response
    ROUTE = "route"           # Routing request
    RESULT = "result"         # Final result
    ERROR = "error"           # Error message
    STATUS = "status"         # Status update
    EVENT = "event"           # System event
    HANDOFF = "handoff"       # Agent handoff


class Priority(Enum):
    """Message priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class AgentType(Enum):
    """Types of agents."""
    MASTER = "master"
    STATS = "stats"
    VIZ = "visualization"
    PREDICT = "prediction"
    SQL = "sql"
    AGGREGATE = "aggregate"


@dataclass
class AgentCapability:
    """Describes an agent's capabilities."""
    name: str
    description: str
    patterns: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)


@dataclass
class MCPMessage:
    """
    MCP Message structure for agent communication.
    
    This is the core message type used for all inter-agent communication.
    Messages are routed through the MCPBus to their target agents.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: MessageType = MessageType.QUERY
    source: str = "user"
    target: str = "master"
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    priority: Priority = Priority.NORMAL
    correlation_id: str = None  # For tracking related messages
    
    def __post_init__(self):
        """Set correlation_id if not provided."""
        if self.correlation_id is None:
            self.correlation_id = self.id
    
    def to_dict(self) -> Dict:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'type': self.type.value,
            'source': self.source,
            'target': self.target,
            'content': self.content,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'correlation_id': self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MCPMessage':
        """Create message from dictionary."""
        return cls(
            id=data.get('id', str(uuid.uuid4())[:8]),
            type=MessageType(data.get('type', 'query')),
            source=data.get('source', 'user'),
            target=data.get('target', 'master'),
            content=data.get('content', ''),
            data=data.get('data', {}),
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(),
            priority=Priority(data.get('priority', 1)),
            correlation_id=data.get('correlation_id')
        )
    
    def create_response(self, content: str, **kwargs) -> 'MCPMessage':
        """Create a response message to this message."""
        return MCPMessage(
            type=MessageType.RESPONSE,
            source=self.target,
            target=self.source,
            content=content,
            correlation_id=self.correlation_id,
            **kwargs
        )


@dataclass
class AgentResponse:
    """
    Standard response from an agent.
    
    All agents return responses in this format for consistency.
    """
    
    content: str = ""
    figure: Any = None
    dataframe: Any = None
    insights: str = None
    suggestions: List[str] = field(default_factory=list)
    agent_name: str = ""
    agent_emoji: str = "🤖"
    success: bool = True
    error: str = None
    execution_time_ms: float = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert response to dictionary for UI rendering."""
        return {
            'content': self.content,
            'figure': self.figure,
            'dataframe': self.dataframe,
            'insights': self.insights,
            'suggestions': self.suggestions,
            'agent': self.agent_name,
            'emoji': self.agent_emoji,
            'success': self.success,
            'error': self.error
        }
    
    def is_error(self) -> bool:
        """Check if response is an error."""
        return not self.success or self.error is not None


class MCPBus:
    """
    Message Bus for agent communication.
    
    The MCPBus is the central routing hub for all agent communication.
    It maintains an agent registry and routes messages to appropriate handlers.
    
    Features:
    - Agent registration and discovery
    - Message routing with priority
    - Message history for debugging
    - Error handling and recovery
    - Broadcast capability
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.message_history: List[MCPMessage] = []
        self.max_history_size: int = 100
        self.middleware: List[Callable] = []
    
    def register_agent(self, name: str, agent: Any, capability: AgentCapability = None):
        """
        Register an agent with the bus.
        
        Args:
            name: Unique agent identifier
            agent: Agent instance
            capability: Optional capability description
        """
        self.agents[name] = agent
        if capability:
            self.agent_capabilities[name] = capability
        logger.debug(f"Registered agent: {name}")
    
    def unregister_agent(self, name: str):
        """Unregister an agent from the bus."""
        if name in self.agents:
            del self.agents[name]
            if name in self.agent_capabilities:
                del self.agent_capabilities[name]
            logger.debug(f"Unregistered agent: {name}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware for message processing."""
        self.middleware.append(middleware)
    
    def _apply_middleware(self, message: MCPMessage) -> MCPMessage:
        """Apply middleware to message."""
        for mw in self.middleware:
            message = mw(message)
        return message
    
    def send(self, message: MCPMessage) -> Optional[AgentResponse]:
        """
        Send a message to target agent and get response.
        
        This is the core routing method that:
        1. Applies middleware
        2. Logs message to history
        3. Routes to target agent
        4. Handles errors
        5. Returns standardized response
        """
        import time
        start_time = time.time()
        
        # Apply middleware
        message = self._apply_middleware(message)
        
        # Log to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history_size:
            self.message_history.pop(0)
        
        target = message.target
        
        # Check if agent exists
        if target not in self.agents:
            logger.error(f"Agent not found: {target}")
            return AgentResponse(
                success=False,
                error=f"Agent '{target}' not found",
                agent_name="System",
                agent_emoji="⚠️"
            )
        
        agent = self.agents[target]
        
        try:
            # Route to agent's process method
            if hasattr(agent, 'process_message'):
                response = agent.process_message(message)
            elif hasattr(agent, 'process'):
                response = agent.process(message.content)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Agent '{target}' has no process method",
                    agent_name="System"
                )
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            
            # Convert dict response to AgentResponse
            if isinstance(response, dict):
                return AgentResponse(
                    content=response.get('content', ''),
                    figure=response.get('figure'),
                    dataframe=response.get('dataframe'),
                    insights=response.get('insights'),
                    suggestions=response.get('suggestions', []),
                    agent_name=response.get('agent', agent.name if hasattr(agent, 'name') else target),
                    agent_emoji=response.get('emoji', agent.emoji if hasattr(agent, 'emoji') else '🤖'),
                    success=True,
                    execution_time_ms=execution_time
                )
            elif isinstance(response, AgentResponse):
                response.execution_time_ms = execution_time
                return response
            else:
                return AgentResponse(
                    content=str(response),
                    agent_name=target,
                    success=True,
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            logger.error(f"Error in agent {target}: {str(e)}")
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=target,
                agent_emoji="❌"
            )
    
    def broadcast(self, message: MCPMessage) -> List[AgentResponse]:
        """Broadcast message to all agents."""
        responses = []
        for name in self.agents:
            msg = MCPMessage(
                type=message.type,
                source=message.source,
                target=name,
                content=message.content,
                data=message.data,
                correlation_id=message.correlation_id
            )
            responses.append(self.send(msg))
        return responses
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent names."""
        return list(self.agents.keys())
    
    def get_agent_capability(self, name: str) -> Optional[AgentCapability]:
        """Get capability description for an agent."""
        return self.agent_capabilities.get(name)
    
    def get_message_history(self, limit: int = 10) -> List[MCPMessage]:
        """Get recent message history."""
        return self.message_history[-limit:]
    
    def clear_history(self):
        """Clear message history."""
        self.message_history = []
