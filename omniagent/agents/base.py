"""
Base agent class for all specialized agents.

Extends MCPServer with common functionality for data agents.
"""

from typing import Any

from omniagent.data.duckdb_engine import DuckDBEngine
from omniagent.mcp.server import MCPServer


class BaseAgent(MCPServer):
    """
    Base class for data analysis agents.
    
    Provides:
    - Access to the DuckDB engine
    - Common utilities for data operations
    - Dataset context management
    """
    
    name: str = "base_agent"
    description: str = "Base agent for data operations"
    
    def __init__(
        self,
        db_engine: DuckDBEngine,
        **kwargs: Any,
    ):
        """
        Initialize the base agent.
        
        Args:
            db_engine: DuckDB engine for data access
            **kwargs: Additional arguments passed to MCPServer
        """
        self.db = db_engine
        super().__init__(**kwargs)
    
    def _get_table_name(self, dataset_id: str | None = None) -> str:
        """
        Get the table name for the current dataset.
        
        For MVP, we assume a single dataset. In the future,
        this would look up the table name from dataset_id.
        """
        # For now, return the first table in the database
        # In production, this would use a dataset registry
        result = self.db.connection.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            LIMIT 1
        """)
        row = result.fetchone()
        if row:
            return row[0]
        raise ValueError("No dataset loaded")
    
    def _validate_columns(
        self,
        table_name: str,
        columns: list[str],
    ) -> tuple[bool, str | None]:
        """
        Validate that columns exist in the table.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        result = self.db.connection.execute(f"DESCRIBE {table_name}")
        valid_columns = {row[0] for row in result.fetchall()}
        
        invalid = [col for col in columns if col not in valid_columns]
        if invalid:
            return False, f"Invalid columns: {', '.join(invalid)}"
        
        return True, None
    
    def _get_numeric_columns(self, table_name: str) -> list[str]:
        """Get list of numeric columns in a table."""
        result = self.db.connection.execute(f"DESCRIBE {table_name}")
        numeric_types = {"BIGINT", "INTEGER", "SMALLINT", "DOUBLE", "FLOAT", "REAL", "DECIMAL"}
        
        return [
            row[0] for row in result.fetchall()
            if any(t in row[1].upper() for t in numeric_types)
        ]
    
    def _get_categorical_columns(self, table_name: str) -> list[str]:
        """Get list of categorical (string) columns in a table."""
        result = self.db.connection.execute(f"DESCRIBE {table_name}")
        string_types = {"VARCHAR", "CHAR", "TEXT", "STRING"}
        
        return [
            row[0] for row in result.fetchall()
            if any(t in row[1].upper() for t in string_types)
        ]
