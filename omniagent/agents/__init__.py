"""
Specialized agents for OmniAgent.

Each agent provides MCP tools for specific functionality:
- SchemaAgent: Dataset structure and metadata
- SQLAgent: Safe SQL query execution
- EDAAgent: Exploratory data analysis
- StatsAgent: Statistical computations
- RegressionAgent: Predictive modeling
- PlotAgent: Visualization generation
"""

from omniagent.agents.base import BaseAgent
from omniagent.agents.schema_agent import SchemaAgent
from omniagent.agents.sql_agent import SQLAgent
from omniagent.agents.eda_agent import EDAAgent
from omniagent.agents.stats_agent import StatsAgent
from omniagent.agents.regression_agent import RegressionAgent
from omniagent.agents.plot_agent import PlotAgent

__all__ = [
    "BaseAgent",
    "SchemaAgent",
    "SQLAgent",
    "EDAAgent",
    "StatsAgent",
    "RegressionAgent",
    "PlotAgent",
]
