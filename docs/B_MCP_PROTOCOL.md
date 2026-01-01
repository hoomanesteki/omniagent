# Message Communication Protocol (MCP)
## Best-in-Class Agent Communication

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Message Types](#message-types)
4. [MCPMessage Structure](#mcpmessage-structure)
5. [MCPBus](#mcpbus)
6. [Agent Response](#agent-response)
7. [Message Flow](#message-flow)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

---

## Overview

The Message Communication Protocol (MCP) is a best-in-class message-passing system designed for multi-agent orchestration. It provides:

- **Typed Messages** - Strongly typed message structures
- **Central Routing** - MCPBus for message routing
- **Agent Registry** - Dynamic agent registration
- **Message History** - Full audit trail
- **Priority Levels** - Message prioritization
- **Middleware Support** - Extensible processing pipeline
- **Error Handling** - Graceful failure recovery

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER QUERY                           │
│                              │                               │
│                              ▼                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   MASTER AGENT                       │    │
│  │                                                      │    │
│  │   ┌───────────┐    ┌───────────┐    ┌───────────┐  │    │
│  │   │  Intent   │───▶│  Router   │───▶│   MCP     │  │    │
│  │   │ Detection │    │  Logic    │    │  Message  │  │    │
│  │   └───────────┘    └───────────┘    │   Bus     │  │    │
│  │                                      └─────┬─────┘  │    │
│  └────────────────────────────────────────────┼────────┘    │
│                                               │              │
│            ┌──────────────────────────────────┼──────────┐  │
│            │              MCP BUS             │          │  │
│            │                                  ▼          │  │
│            │    ┌────────┐  ┌────────┐  ┌────────┐      │  │
│            │    │ Stats  │  │  Viz   │  │  Agg   │      │  │
│            │    │ Agent  │  │ Agent  │  │ Agent  │      │  │
│            │    └────────┘  └────────┘  └────────┘      │  │
│            │    ┌────────┐  ┌────────┐                  │  │
│            │    │Predict │  │  SQL   │                  │  │
│            │    │ Agent  │  │ Agent  │                  │  │
│            │    └────────┘  └────────┘                  │  │
│            └─────────────────────────────────────────────┘  │
│                              │                               │
│                              ▼                               │
│                    ┌─────────────────┐                      │
│                    │ AGENT RESPONSE  │                      │
│                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Message Types

```python
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
```

### When to Use Each Type

| Type | Use Case |
|------|----------|
| QUERY | Initial user request to an agent |
| RESPONSE | Agent's reply to a query |
| ROUTE | Redirect message to another agent |
| RESULT | Final aggregated result |
| ERROR | Error notification |
| STATUS | Progress or status update |
| EVENT | System-level event (startup, shutdown) |
| HANDOFF | Transfer control to another agent |

---

## MCPMessage Structure

```python
@dataclass
class MCPMessage:
    """Core message structure for agent communication."""
    
    id: str                    # Unique message ID (auto-generated)
    type: MessageType          # Message type
    source: str                # Sending agent name
    target: str                # Target agent name
    content: str               # Message content/query
    data: Dict[str, Any]       # Additional structured data
    metadata: Dict[str, Any]   # Message metadata
    timestamp: datetime        # Creation timestamp
    priority: Priority         # Message priority level
    correlation_id: str        # For tracking related messages
```

### Priority Levels

```python
class Priority(Enum):
    LOW = 0       # Background tasks
    NORMAL = 1    # Standard requests
    HIGH = 2      # Important requests
    CRITICAL = 3  # System-critical
```

### Creating Messages

```python
from mcp.protocol import MCPMessage, MessageType, Priority

# Basic message
msg = MCPMessage(
    type=MessageType.QUERY,
    source='master',
    target='stats',
    content='show statistics'
)

# Message with data
msg = MCPMessage(
    type=MessageType.QUERY,
    source='master',
    target='viz',
    content='histogram of age',
    data={'column': 'age', 'bins': 30},
    priority=Priority.HIGH
)

# Convert to dict
msg_dict = msg.to_dict()

# Create from dict
msg2 = MCPMessage.from_dict(msg_dict)

# Create response message
response = msg.create_response("Here are the statistics...")
```

---

## MCPBus

The MCPBus is the central message routing hub.

### Initialization

```python
from mcp.protocol import MCPBus

bus = MCPBus()
```

### Agent Registration

```python
# Register an agent
bus.register_agent('stats', stats_agent)
bus.register_agent('viz', viz_agent)

# With capability description
from mcp.protocol import AgentCapability

capability = AgentCapability(
    name="Stats Agent",
    description="Statistical analysis and data quality",
    patterns=['mean', 'median', 'std', 'statistics'],
    examples=['Show statistics', 'Mean of price']
)
bus.register_agent('stats', stats_agent, capability)

# Unregister
bus.unregister_agent('stats')

# List registered agents
agents = bus.get_registered_agents()
```

### Sending Messages

```python
from mcp.protocol import MCPMessage, MessageType

# Create and send message
msg = MCPMessage(
    type=MessageType.QUERY,
    source='master',
    target='stats',
    content='show statistics'
)

response = bus.send(msg)

# Response is an AgentResponse object
if response.success:
    print(response.content)
else:
    print(f"Error: {response.error}")
```

### Broadcasting

```python
# Send message to all agents
msg = MCPMessage(
    type=MessageType.STATUS,
    source='master',
    target='*',
    content='System health check'
)

responses = bus.broadcast(msg)
for resp in responses:
    print(f"{resp.agent_name}: {resp.success}")
```

### Middleware

```python
def logging_middleware(message: MCPMessage) -> MCPMessage:
    """Log all messages."""
    print(f"[MCP] {message.source} -> {message.target}: {message.content}")
    return message

def timestamp_middleware(message: MCPMessage) -> MCPMessage:
    """Add processing timestamp."""
    message.metadata['processed_at'] = datetime.now().isoformat()
    return message

# Add middleware
bus.add_middleware(logging_middleware)
bus.add_middleware(timestamp_middleware)
```

### Message History

```python
# Get recent messages
history = bus.get_message_history(limit=10)

for msg in history:
    print(f"{msg.timestamp}: {msg.source} -> {msg.target}")

# Clear history
bus.clear_history()
```

---

## Agent Response

```python
@dataclass
class AgentResponse:
    """Standard response from an agent."""
    
    content: str = ""              # Markdown response content
    figure: Any = None             # Plotly figure
    dataframe: Any = None          # Pandas DataFrame
    insights: str = None           # Key insights text
    suggestions: List[str] = []    # Suggested next actions
    agent_name: str = ""           # Responding agent name
    agent_emoji: str = "🤖"        # Agent emoji
    success: bool = True           # Success flag
    error: str = None              # Error message if failed
    execution_time_ms: float = 0   # Processing time
    metadata: Dict = {}            # Additional metadata
```

### Working with Responses

```python
response = bus.send(message)

# Check success
if response.success:
    # Access content
    print(response.content)
    
    # Display figure
    if response.figure:
        response.figure.show()
    
    # Show dataframe
    if response.dataframe is not None:
        print(response.dataframe)
    
    # Show insights
    if response.insights:
        print(response.insights)
    
    # Get suggestions
    for sug in response.suggestions:
        print(f"  - {sug}")
else:
    print(f"Error: {response.error}")

# Convert to dict for UI
result = response.to_dict()
```

---

## Message Flow

### Standard Query Flow

```
1. User enters query
2. Master Agent receives query
3. Master Agent detects intent
4. Master Agent creates MCPMessage
5. MCPBus routes to target agent
6. Target agent processes query
7. Target agent returns AgentResponse
8. MCPBus wraps response
9. Master Agent receives response
10. UI renders response
```

### Sequence Diagram

```
User          Master         MCPBus        StatsAgent
  │              │              │              │
  │──"mean"──────▶              │              │
  │              │              │              │
  │              │──MCPMessage──▶              │
  │              │              │──process()───▶
  │              │              │              │
  │              │              │◀─Response────│
  │              │◀─AgentResponse│              │
  │◀──Result─────│              │              │
```

---

## Best Practices

### 1. Message Design

```python
# ✅ Good: Specific, includes context
msg = MCPMessage(
    type=MessageType.QUERY,
    source='master',
    target='stats',
    content='calculate mean of price column',
    data={'column': 'price', 'operation': 'mean'},
    metadata={'user_session': 'abc123'}
)

# ❌ Bad: Vague, no context
msg = MCPMessage(content='do something')
```

### 2. Error Handling

```python
# Always check response success
response = bus.send(msg)
if not response.success:
    # Log error
    logger.error(f"Agent error: {response.error}")
    # Return graceful fallback
    return format_error(response.error)
```

### 3. Correlation IDs

```python
# Use correlation IDs to track related messages
original = MCPMessage(
    type=MessageType.QUERY,
    source='user',
    target='master',
    content='complex analysis'
)

# Related follow-up
followup = MCPMessage(
    type=MessageType.QUERY,
    source='master',
    target='viz',
    content='create chart',
    correlation_id=original.correlation_id  # Same ID
)
```

### 4. Agent Registration

```python
# Register with capabilities for discovery
bus.register_agent('stats', stats_agent, AgentCapability(
    name="Statistics Agent",
    description="Statistical analysis",
    patterns=['mean', 'median', 'std', 'variance'],
    examples=['Mean of price', 'Show statistics']
))
```

---

## Examples

### Example 1: Simple Query

```python
from mcp.protocol import MCPBus, MCPMessage, MessageType

# Setup
bus = MCPBus()
bus.register_agent('stats', StatsAgent(df, analyzer))

# Send query
msg = MCPMessage(
    type=MessageType.QUERY,
    source='user',
    target='stats',
    content='show statistics'
)

response = bus.send(msg)
print(response.content)
```

### Example 2: Multi-Agent Workflow

```python
# Step 1: Get statistics
stats_msg = MCPMessage(
    type=MessageType.QUERY,
    source='master',
    target='stats',
    content='describe price'
)
stats_resp = bus.send(stats_msg)

# Step 2: Visualize based on stats
viz_msg = MCPMessage(
    type=MessageType.QUERY,
    source='master',
    target='viz',
    content='histogram of price',
    data={'stats': stats_resp.content}
)
viz_resp = bus.send(viz_msg)

# Combine results
final = {
    'stats': stats_resp.content,
    'figure': viz_resp.figure
}
```

### Example 3: Error Recovery

```python
response = bus.send(msg)

if not response.success:
    # Try fallback agent
    fallback_msg = MCPMessage(
        type=MessageType.QUERY,
        source='master',
        target='sql',
        content='show columns'
    )
    fallback_resp = bus.send(fallback_msg)
    
    if fallback_resp.success:
        return fallback_resp
    else:
        return AgentResponse(
            success=False,
            error="All agents failed",
            content="## ❌ Error\n\nUnable to process request."
        )
```

---

## Performance Considerations

1. **Message Size**: Keep `data` field small
2. **History Limit**: Default 100 messages
3. **Middleware**: Keep middleware lightweight
4. **Timeouts**: Implement timeout handling for long operations

---

*Last updated: 2026-01-01*
