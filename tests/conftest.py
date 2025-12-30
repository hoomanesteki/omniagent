"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path
import sys

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def db_engine():
    """Create a shared DuckDB engine for tests."""
    from omniagent.data.duckdb_engine import DuckDBEngine
    return DuckDBEngine()


@pytest.fixture(scope="session")
def sample_data_path():
    """Get path to sample data."""
    paths = [
        Path("data/samples/fitness_tracker.csv"),
        Path("data/samples/ecommerce_sales.csv"),
        Path("data/samples/employee_data.csv"),
        Path("data/samples/housing.csv"),
    ]
    for p in paths:
        if p.exists():
            return p
    pytest.skip("No sample data found")


@pytest.fixture(scope="session")
def dataset_profile(db_engine, sample_data_path):
    """Load sample dataset and return profile."""
    from omniagent.data.loader import DataLoader
    loader = DataLoader(db_engine=db_engine)
    return loader.load_csv_path(sample_data_path)


@pytest.fixture
def mcp_client(db_engine, dataset_profile):
    """Create MCP client with all agents registered."""
    from omniagent.mcp.client import MCPClient
    from omniagent.agents import (
        SchemaAgent, SQLAgent, EDAAgent,
        StatsAgent, RegressionAgent, PlotAgent,
    )
    
    client = MCPClient()
    
    for AgentClass in [SchemaAgent, SQLAgent, EDAAgent, StatsAgent, RegressionAgent, PlotAgent]:
        agent = AgentClass(db_engine)
        agent._current_table = dataset_profile.metadata.table_name
        client.register_agent(agent)
    
    return client
