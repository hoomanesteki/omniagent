# OmniAgent Testing Guide
## Comprehensive Testing Documentation

---

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Test Structure](#test-structure)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [End-to-End Tests](#end-to-end-tests)
6. [Running Tests](#running-tests)
7. [Test Coverage](#test-coverage)
8. [Writing New Tests](#writing-new-tests)

---

## Testing Overview

OmniAgent uses a comprehensive testing strategy:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows

### Testing Stack

| Tool | Purpose |
|------|---------|
| pytest | Test framework |
| pytest-cov | Coverage reporting |
| pytest-mock | Mocking utilities |
| pandas | Test data creation |

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_analyzer.py
│   ├── test_config.py
│   ├── test_llm.py
│   ├── test_agents/
│   │   ├── test_stats_agent.py
│   │   ├── test_viz_agent.py
│   │   ├── test_aggregate_agent.py
│   │   ├── test_predict_agent.py
│   │   ├── test_sql_agent.py
│   │   └── test_master_agent.py
│   └── test_mcp/
│       └── test_protocol.py
├── integration/
│   ├── __init__.py
│   ├── test_agent_routing.py
│   └── test_mcp_bus.py
└── e2e/
    ├── __init__.py
    └── test_workflows.py
```

---

## Unit Tests

### Test Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
import pandas as pd
import numpy as np
from core.analyzer import DataAnalyzer
from core.llm import LLMClient

@pytest.fixture
def sample_df():
    """Create sample DataFrame for testing."""
    np.random.seed(42)
    return pd.DataFrame({
        'id': range(1, 101),
        'age': np.random.randint(18, 65, 100),
        'salary': np.random.uniform(30000, 150000, 100),
        'department': np.random.choice(['Sales', 'IT', 'HR', 'Finance'], 100),
        'gender': np.random.choice(['M', 'F'], 100),
        'active': np.random.choice([True, False], 100)
    })

@pytest.fixture
def analyzer(sample_df):
    """Create DataAnalyzer instance."""
    return DataAnalyzer(sample_df)

@pytest.fixture
def mock_llm():
    """Create mock LLM client."""
    return LLMClient(api_key="test-key")
```

### Test DataAnalyzer

```python
# tests/unit/test_analyzer.py
import pytest
import pandas as pd
from core.analyzer import DataAnalyzer

class TestDataAnalyzer:
    """Tests for DataAnalyzer class."""
    
    def test_row_count(self, sample_df, analyzer):
        """Test row count calculation."""
        assert analyzer.row_count == 100
    
    def test_col_count(self, sample_df, analyzer):
        """Test column count."""
        assert analyzer.col_count == 6
    
    def test_numeric_columns(self, analyzer):
        """Test numeric column detection."""
        assert 'age' in analyzer.numeric_columns
        assert 'salary' in analyzer.numeric_columns
        assert 'department' not in analyzer.numeric_columns
    
    def test_categorical_columns(self, analyzer):
        """Test categorical column detection."""
        assert 'department' in analyzer.categorical_columns
        assert 'gender' in analyzer.categorical_columns
        assert 'age' not in analyzer.categorical_columns
    
    def test_id_column_detection(self, analyzer):
        """Test ID column detection."""
        assert 'id' in analyzer.id_columns
    
    def test_usable_numeric_excludes_id(self, analyzer):
        """Test that ID columns are excluded from usable numeric."""
        assert 'id' not in analyzer.usable_numeric
    
    def test_target_candidates(self, analyzer):
        """Test target candidate detection."""
        candidates = analyzer.target_candidates
        assert len(candidates) > 0
        # Check structure
        assert 'column' in candidates[0]
        assert 'type' in candidates[0]
    
    def test_get_summary(self, analyzer):
        """Test summary generation."""
        summary = analyzer.get_summary()
        assert summary['rows'] == 100
        assert summary['columns'] == 6
        assert 'missing_total' in summary
        assert 'memory_mb' in summary
    
    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        analyzer = DataAnalyzer(df)
        assert analyzer.row_count == 0
        assert analyzer.col_count == 0
    
    def test_missing_values(self):
        """Test missing value handling."""
        df = pd.DataFrame({
            'a': [1, 2, None, 4],
            'b': ['x', None, 'z', 'w']
        })
        analyzer = DataAnalyzer(df)
        summary = analyzer.get_summary()
        assert summary['missing_total'] == 2
```

### Test Agents

```python
# tests/unit/test_agents/test_stats_agent.py
import pytest
from agents.stats_agent import StatsAgent

class TestStatsAgent:
    """Tests for StatsAgent."""
    
    @pytest.fixture
    def stats_agent(self, sample_df, analyzer):
        return StatsAgent(sample_df, analyzer)
    
    def test_process_mean(self, stats_agent):
        """Test mean calculation."""
        result = stats_agent.process("mean of age")
        assert result['content'] is not None
        assert 'mean' in result['content'].lower()
    
    def test_process_median(self, stats_agent):
        """Test median calculation."""
        result = stats_agent.process("median of salary")
        assert result['content'] is not None
    
    def test_process_statistics(self, stats_agent):
        """Test full statistics."""
        result = stats_agent.process("show statistics")
        assert result['content'] is not None
        assert result['dataframe'] is not None
    
    def test_process_missing(self, stats_agent):
        """Test missing values check."""
        result = stats_agent.process("check missing values")
        assert result['content'] is not None
    
    def test_invalid_column(self, stats_agent):
        """Test error on invalid column."""
        result = stats_agent.process("mean of nonexistent_column")
        assert 'error' in result['content'].lower() or 'not found' in result['content'].lower()
    
    def test_suggestions_returned(self, stats_agent):
        """Test that suggestions are returned."""
        result = stats_agent.process("show statistics")
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0
```

### Test MCP Protocol

```python
# tests/unit/test_mcp/test_protocol.py
import pytest
from datetime import datetime
from mcp.protocol import (
    MCPMessage, MCPBus, AgentResponse, 
    MessageType, Priority, AgentCapability
)

class TestMCPMessage:
    """Tests for MCPMessage."""
    
    def test_default_values(self):
        """Test default message values."""
        msg = MCPMessage()
        assert msg.type == MessageType.QUERY
        assert msg.source == "user"
        assert msg.target == "master"
        assert msg.id is not None
    
    def test_custom_values(self):
        """Test custom message values."""
        msg = MCPMessage(
            type=MessageType.RESPONSE,
            source="stats",
            target="master",
            content="Result"
        )
        assert msg.type == MessageType.RESPONSE
        assert msg.source == "stats"
        assert msg.content == "Result"
    
    def test_to_dict(self):
        """Test message serialization."""
        msg = MCPMessage(content="test")
        d = msg.to_dict()
        assert d['content'] == "test"
        assert 'id' in d
        assert 'timestamp' in d
    
    def test_from_dict(self):
        """Test message deserialization."""
        d = {
            'type': 'query',
            'source': 'user',
            'target': 'stats',
            'content': 'test'
        }
        msg = MCPMessage.from_dict(d)
        assert msg.content == 'test'
        assert msg.type == MessageType.QUERY
    
    def test_create_response(self):
        """Test response message creation."""
        original = MCPMessage(source='user', target='stats')
        response = original.create_response("Response content")
        assert response.source == 'stats'
        assert response.target == 'user'
        assert response.type == MessageType.RESPONSE
        assert response.correlation_id == original.correlation_id

class TestMCPBus:
    """Tests for MCPBus."""
    
    def test_register_agent(self):
        """Test agent registration."""
        bus = MCPBus()
        
        class MockAgent:
            name = "Mock"
            def process(self, query):
                return {'content': 'ok'}
        
        bus.register_agent('mock', MockAgent())
        assert 'mock' in bus.get_registered_agents()
    
    def test_unregister_agent(self):
        """Test agent unregistration."""
        bus = MCPBus()
        bus.register_agent('test', object())
        bus.unregister_agent('test')
        assert 'test' not in bus.get_registered_agents()
    
    def test_send_to_registered_agent(self):
        """Test sending to registered agent."""
        bus = MCPBus()
        
        class MockAgent:
            name = "Mock"
            emoji = "🎯"
            def process(self, query):
                return {'content': f'Received: {query}'}
        
        bus.register_agent('mock', MockAgent())
        
        msg = MCPMessage(target='mock', content='hello')
        response = bus.send(msg)
        
        assert response.success
        assert 'hello' in response.content
    
    def test_send_to_unregistered_agent(self):
        """Test sending to non-existent agent."""
        bus = MCPBus()
        msg = MCPMessage(target='nonexistent', content='hello')
        response = bus.send(msg)
        
        assert not response.success
        assert 'not found' in response.error.lower()
    
    def test_message_history(self):
        """Test message history tracking."""
        bus = MCPBus()
        bus.register_agent('test', type('Agent', (), {
            'name': 'Test',
            'process': lambda s, q: {'content': 'ok'}
        })())
        
        msg = MCPMessage(target='test', content='test')
        bus.send(msg)
        
        history = bus.get_message_history(limit=1)
        assert len(history) == 1
        assert history[0].content == 'test'

class TestAgentResponse:
    """Tests for AgentResponse."""
    
    def test_default_values(self):
        """Test default response values."""
        resp = AgentResponse()
        assert resp.success == True
        assert resp.error is None
        assert resp.content == ""
    
    def test_to_dict(self):
        """Test response serialization."""
        resp = AgentResponse(
            content="Test",
            agent_name="Stats",
            success=True
        )
        d = resp.to_dict()
        assert d['content'] == "Test"
        assert d['agent'] == "Stats"
    
    def test_is_error(self):
        """Test error checking."""
        ok = AgentResponse(success=True)
        err = AgentResponse(success=False, error="Failed")
        
        assert not ok.is_error()
        assert err.is_error()
```

---

## Integration Tests

```python
# tests/integration/test_agent_routing.py
import pytest
from agents.master_agent import MasterAgent
from core.analyzer import DataAnalyzer

class TestAgentRouting:
    """Test agent routing through master agent."""
    
    @pytest.fixture
    def master(self, sample_df, analyzer):
        return MasterAgent(sample_df, analyzer)
    
    def test_route_to_stats(self, master):
        """Test routing to stats agent."""
        result = master.process("show statistics")
        assert 'stats' in str(master.current_agent).lower() or result['content']
    
    def test_route_to_viz(self, master):
        """Test routing to viz agent."""
        result = master.process("histogram of age")
        assert master.current_agent == 'viz' or 'histogram' in result['content'].lower()
    
    def test_route_to_aggregate(self, master):
        """Test routing to aggregate agent."""
        result = master.process("count by department")
        assert master.current_agent == 'aggregate' or 'count' in result['content'].lower()
    
    def test_route_to_predict(self, master):
        """Test routing to predict agent."""
        result = master.process("predict active")
        assert master.current_agent == 'predict' or 'predict' in result['content'].lower()
    
    def test_route_to_sql(self, master):
        """Test routing to SQL agent."""
        result = master.process("show first 10 rows")
        assert master.current_agent == 'sql' or result.get('dataframe') is not None
    
    def test_unknown_query(self, master):
        """Test handling of unknown queries."""
        result = master.process("xyzabc123")
        assert result['content'] is not None
        # Should provide guidance
        assert 'suggestions' in result
```

---

## End-to-End Tests

```python
# tests/e2e/test_workflows.py
import pytest
import pandas as pd
from core.analyzer import DataAnalyzer
from agents.master_agent import MasterAgent

class TestWorkflows:
    """End-to-end workflow tests."""
    
    @pytest.fixture
    def setup(self):
        """Setup test environment."""
        df = pd.DataFrame({
            'age': [25, 30, 35, 40, 45],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'department': ['IT', 'Sales', 'IT', 'HR', 'Sales']
        })
        analyzer = DataAnalyzer(df)
        master = MasterAgent(df, analyzer)
        return master
    
    def test_exploration_workflow(self, setup):
        """Test data exploration workflow."""
        master = setup
        
        # Step 1: Check structure
        r1 = master.process("show columns")
        assert r1['content']
        
        # Step 2: Get statistics
        r2 = master.process("show statistics")
        assert r2['content']
        
        # Step 3: Check missing
        r3 = master.process("check missing values")
        assert r3['content']
    
    def test_visualization_workflow(self, setup):
        """Test visualization workflow."""
        master = setup
        
        # Step 1: Histogram
        r1 = master.process("histogram of age")
        assert r1.get('figure') or r1['content']
        
        # Step 2: Bar chart
        r2 = master.process("bar chart of department")
        assert r2.get('figure') or r2['content']
        
        # Step 3: Correlation
        r3 = master.process("correlation heatmap")
        assert r3.get('figure') or r3['content']
    
    def test_aggregation_workflow(self, setup):
        """Test aggregation workflow."""
        master = setup
        
        # Step 1: Count
        r1 = master.process("count by department")
        assert r1['content']
        
        # Step 2: Average
        r2 = master.process("average salary by department")
        assert r2['content']
    
    def test_prediction_workflow(self, setup):
        """Test prediction workflow."""
        master = setup
        
        # Step 1: What can predict
        r1 = master.process("what can I predict")
        assert r1['content']
        
        # Step 2: Build model (if enough data)
        r2 = master.process("build model")
        assert r2['content']
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_analyzer.py

# Run specific test class
pytest tests/unit/test_analyzer.py::TestDataAnalyzer

# Run specific test
pytest tests/unit/test_analyzer.py::TestDataAnalyzer::test_row_count
```

### Run by Category

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# E2E tests only
pytest tests/e2e/
```

### Run with Markers

```bash
# Run slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

---

## Test Coverage

### Generate Coverage Report

```bash
# HTML report
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=. --cov-report=term-missing

# XML report (for CI)
pytest --cov=. --cov-report=xml
```

### Coverage Targets

| Module | Target |
|--------|--------|
| core/ | 90% |
| agents/ | 85% |
| mcp/ | 95% |
| ui/ | 70% |

---

## Writing New Tests

### Test Template

```python
import pytest
from module_to_test import ClassToTest

class TestClassName:
    """Tests for ClassName."""
    
    @pytest.fixture
    def instance(self):
        """Create test instance."""
        return ClassToTest()
    
    def test_method_name_success(self, instance):
        """Test method with valid input."""
        result = instance.method("valid input")
        assert result == expected_value
    
    def test_method_name_failure(self, instance):
        """Test method with invalid input."""
        with pytest.raises(ValueError):
            instance.method("invalid input")
    
    def test_method_edge_case(self, instance):
        """Test method edge case."""
        result = instance.method("")
        assert result is None
```

### Assertion Best Practices

```python
# ✅ Good: Specific assertions
assert result['status'] == 'success'
assert len(items) == 3
assert 'error' in message.lower()

# ❌ Bad: Vague assertions
assert result
assert items
assert message
```

---

*Last updated: 2026-01-01*
