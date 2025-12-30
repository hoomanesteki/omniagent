"""
Data layer for OmniAgent.

Handles:
- CSV/Parquet file loading
- DuckDB database management
- Schema inference
- Data storage
"""

from omniagent.data.loader import DataLoader
from omniagent.data.duckdb_engine import DuckDBEngine
from omniagent.data.schema_inference import SchemaInferrer

__all__ = [
    "DataLoader",
    "DuckDBEngine",
    "SchemaInferrer",
]
