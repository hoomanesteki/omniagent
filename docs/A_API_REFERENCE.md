# OmniAgent API Documentation
## Complete API Reference

---

## Table of Contents

1. [Overview](#overview)
2. [Core Modules](#core-modules)
3. [Agent APIs](#agent-apis)
4. [MCP Protocol](#mcp-protocol)
5. [UI Components](#ui-components)
6. [Data Structures](#data-structures)
7. [Error Handling](#error-handling)

---

## Overview

OmniAgent exposes a clean internal API for agent communication and data processing. The architecture follows a message-passing pattern using the Message Communication Protocol (MCP).

### Architecture Layers

```
┌─────────────────────────────────────┐
│           UI Layer (Streamlit)       │
├─────────────────────────────────────┤
│         Master Agent (Router)        │
├─────────────────────────────────────┤
│    MCP Bus (Message Communication)   │
├─────────────────────────────────────┤
│         Specialized Agents           │
│  Stats | Viz | Agg | Predict | SQL  │
├─────────────────────────────────────┤
│      Core (Config, Analyzer, LLM)    │
└─────────────────────────────────────┘
```

---

## Core Modules

### Config (`core/config.py`)

Configuration management for the application.

```python
from core.config import Config

# Access configuration
api_key = Config.GROQ_API_KEY
data_dir = Config.DATA_DIR
colors = Config.COLORS
```

**Available Settings:**

| Setting | Type | Description |
|---------|------|-------------|
| `AUTHOR` | str | Application author |
| `AUTHOR_URL` | str | Author's website |
| `BASE_DIR` | Path | Application root directory |
| `DATA_DIR` | Path | Data storage directory |
| `SAMPLES_DIR` | Path | Sample datasets directory |
| `GROQ_API_KEY` | str | LLM API key |
| `LLM_MODEL` | str | LLM model name |
| `LLM_MAX_TOKENS` | int | Max tokens for LLM |
| `LLM_TEMPERATURE` | float | LLM temperature |
| `PAGE_TITLE` | str | Streamlit page title |
| `COLORS` | List[str] | Chart color palette |

---

### DataAnalyzer (`core/analyzer.py`)

Analyzes DataFrames and provides metadata.

```python
from core.analyzer import DataAnalyzer
import pandas as pd

df = pd.read_csv('data.csv')
analyzer = DataAnalyzer(df)

# Access properties
print(analyzer.row_count)          # Number of rows
print(analyzer.col_count)          # Number of columns
print(analyzer.usable_numeric)     # List of numeric columns
print(analyzer.usable_categorical) # List of categorical columns
print(analyzer.target_candidates)  # Suggested ML targets

# Get summary
summary = analyzer.get_summary()
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `df` | DataFrame | Source dataframe |
| `row_count` | int | Number of rows |
| `col_count` | int | Number of columns |
| `numeric_columns` | List[str] | All numeric columns |
| `categorical_columns` | List[str] | All categorical columns |
| `usable_numeric` | List[str] | Numeric columns for analysis |
| `usable_categorical` | List[str] | Categorical columns for analysis |
| `id_columns` | List[str] | Detected ID columns |
| `target_candidates` | List[Dict] | Suggested prediction targets |
| `memory_usage` | float | Memory usage in MB |

**Methods:**

```python
def get_summary() -> Dict[str, Any]:
    """
    Returns comprehensive dataset summary.
    
    Returns:
        dict with keys: rows, columns, numeric_columns, 
        categorical_columns, missing_total, id_columns, memory_mb
    """
```

---

### LLMClient (`core/llm.py`)

Interface to Groq LLM for AI-enhanced responses.

```python
from core.llm import LLMClient

llm = LLMClient(api_key="your-key")

# Check if active
if llm.is_active():
    response = llm.understand_query("what is the average?", context)
    enhanced = llm.enhance_response(base_response, context)

# Toggle AI mode
llm.toggle(enabled=True)
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `is_active()` | - | bool | Check if LLM is available |
| `toggle(enabled)` | bool | - | Enable/disable LLM |
| `understand_query(query, context)` | str, str | str | Get LLM understanding |
| `enhance_response(response, context)` | str, str | str | Enhance response with LLM |

---

## Agent APIs

### BaseAgent (`agents/base.py`)

Abstract base class for all agents.

```python
from agents.base import BaseAgent

class CustomAgent(BaseAgent):
    name = "Custom Agent"
    emoji = "🎯"
    description = "My custom agent"
    
    def process(self, query: str) -> Dict[str, Any]:
        # Implement processing logic
        return {
            'content': 'Response content',
            'figure': None,
            'dataframe': None,
            'insights': 'Key insights',
            'suggestions': ['Next action 1', 'Next action 2']
        }
```

**Required Methods:**

```python
def process(self, query: str) -> Dict[str, Any]:
    """
    Process user query and return response.
    
    Args:
        query: User's natural language query
        
    Returns:
        Dict with keys: content, figure, dataframe, insights, suggestions
    """
```

**Helper Methods:**

```python
def find_column(self, name: str) -> Optional[str]:
    """Find column by fuzzy name matching."""

def format_error(self, message: str) -> Dict[str, Any]:
    """Format error response."""

def get_suggestions(self) -> List[str]:
    """Get context-aware suggestions."""
```

---

### MasterAgent (`agents/master_agent.py`)

Central orchestrator that routes queries to specialized agents.

```python
from agents.master_agent import MasterAgent

master = MasterAgent(df, analyzer, llm)
result = master.process("show statistics")
```

**Pattern Matching:**

The Master Agent uses pattern matching to detect intent:

```python
PATTERNS = {
    'aggregate': ['group by', 'count by', 'sum by', ...],
    'predict': ['predict', 'model', 'train', ...],
    'stats': ['mean', 'median', 'statistics', ...],
    'histogram': ['histogram', 'distribution', ...],
    # ... more patterns
}
```

---

### StatsAgent (`agents/stats_agent.py`)

Statistical analysis and data quality checks.

```python
from agents.stats_agent import StatsAgent

stats = StatsAgent(df, analyzer)
result = stats.process("mean of price")
```

**Supported Operations:**

| Operation | Example Query |
|-----------|---------------|
| Mean | "mean of price", "average sales" |
| Median | "median of age" |
| Std Dev | "std of revenue", "standard deviation" |
| Min/Max | "min of price", "maximum sales" |
| Percentiles | "25th percentile of age" |
| Describe | "describe price" |
| Missing | "check missing values" |
| Statistics | "show statistics" |

---

### VizAgent (`agents/viz_agent.py`)

Visualization and charting.

```python
from agents.viz_agent import VizAgent

viz = VizAgent(df, analyzer)
result = viz.process("histogram of age")
# result['figure'] contains Plotly figure
```

**Supported Charts:**

| Chart | Example Query |
|-------|---------------|
| Histogram | "histogram of age" |
| Bar Chart | "bar chart of category" |
| Scatter Plot | "scatter price vs quantity" |
| Box Plot | "box plot of salary" |
| Heatmap | "correlation heatmap" |
| Pie Chart | "pie chart of status" |

---

### AggregateAgent (`agents/aggregate_agent.py`)

Data aggregation and groupby operations.

```python
from agents.aggregate_agent import AggregateAgent

agg = AggregateAgent(df, analyzer)
result = agg.process("count by gender")
```

**Supported Operations:**

| Operation | Example Query |
|-----------|---------------|
| Count | "count by gender" |
| Sum | "sum sales by region" |
| Average | "average price by category" |
| Max | "max revenue by month" |
| Min | "min cost by department" |
| Group | "group by status" |

---

### PredictAgent (`agents/predict_agent.py`)

Machine learning model building and predictions.

```python
from agents.predict_agent import PredictAgent

predict = PredictAgent(df, analyzer)
result = predict.process("predict churn")
```

**Supported Operations:**

| Operation | Example Query |
|-----------|---------------|
| Predict | "predict churn" |
| Build Model | "build model" |
| Feature Importance | "feature importance" |
| What Can I Predict | "what can I predict?" |

---

### SQLAgent (`agents/sql_agent.py`)

Data preview and schema exploration.

```python
from agents.sql_agent import SQLAgent

sql = SQLAgent(df, analyzer)
result = sql.process("show first 10 rows")
```

**Supported Operations:**

| Operation | Example Query |
|-----------|---------------|
| Head | "show first 10 rows" |
| Tail | "show last 10 rows" |
| Sample | "random sample" |
| Columns | "show columns" |
| Schema | "data structure" |

---

## MCP Protocol

See `docs/B_MCP_PROTOCOL.md` for complete MCP documentation.

---

## Data Structures

### Agent Response

All agents return responses in this format:

```python
{
    'content': str,           # Markdown content
    'figure': plotly.Figure,  # Optional Plotly figure
    'dataframe': pd.DataFrame, # Optional DataFrame
    'insights': str,          # Key insights
    'suggestions': List[str], # Next action suggestions
    'agent': str,             # Agent name
    'emoji': str              # Agent emoji
}
```

### MCPMessage

```python
@dataclass
class MCPMessage:
    id: str                    # Unique message ID
    type: MessageType          # QUERY, RESPONSE, ERROR
    source: str                # Sending agent
    target: str                # Target agent
    content: str               # Message content
    data: Dict[str, Any]       # Additional data
    metadata: Dict[str, Any]   # Metadata
    timestamp: datetime        # Message timestamp
    priority: Priority         # Message priority
    correlation_id: str        # For tracking
```

---

## Error Handling

All agents return errors in a consistent format:

```python
{
    'content': '## ❌ Error\n\nError message here',
    'insights': None,
    'suggestions': ['Help', 'Try again']
}
```

To create an error response from an agent:

```python
return self.format_error("Column 'xyz' not found")
```

---

## Usage Example

```python
import pandas as pd
from core.analyzer import DataAnalyzer
from core.llm import LLMClient
from agents.master_agent import MasterAgent

# Load data
df = pd.read_csv('data.csv')

# Initialize
analyzer = DataAnalyzer(df)
llm = LLMClient(api_key="...")
master = MasterAgent(df, analyzer, llm)

# Process queries
result1 = master.process("show statistics")
result2 = master.process("histogram of age")
result3 = master.process("predict churn")

# Access results
print(result1['content'])  # Markdown content
fig = result2['figure']    # Plotly figure
fig.show()
```

---

*Last updated: 2026-01-01*
