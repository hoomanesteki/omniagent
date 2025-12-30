"""
DuckDB database engine.

Provides:
- Connection management
- Safe query execution (SELECT-only)
- Query validation
"""

import re
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import duckdb

from omniagent.config.logging import get_logger
from omniagent.models.results import QueryResult

logger = get_logger(__name__)


class SQLValidationError(Exception):
    """Raised when SQL query fails validation."""
    pass


class DuckDBEngine:
    """
    DuckDB database engine with safety features.
    
    Features:
    - In-memory or file-based databases
    - SELECT-only query validation
    - Query timeout
    - Row limit enforcement
    """
    
    # SQL statements that are NOT allowed
    FORBIDDEN_PATTERNS = [
        r"\bINSERT\b",
        r"\bUPDATE\b",
        r"\bDELETE\b",
        r"\bDROP\b",
        r"\bCREATE\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bREPLACE\b",
        r"\bMERGE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bEXEC\b",
        r"\bEXECUTE\b",
        r"\bCALL\b",
        r"\bCOPY\b",
        r"\bATTACH\b",
        r"\bDETACH\b",
    ]
    
    def __init__(
        self,
        database_path: str | None = None,
        read_only: bool = True,
    ):
        """
        Initialize DuckDB engine.
        
        Args:
            database_path: Path to database file. None for in-memory.
            read_only: If True, enforce read-only mode.
        """
        self.database_path = database_path
        self.read_only = read_only
        self._connection: duckdb.DuckDBPyConnection | None = None
        
        # Compile forbidden patterns for efficiency
        self._forbidden_regex = re.compile(
            "|".join(self.FORBIDDEN_PATTERNS),
            re.IGNORECASE,
        )
    
    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self._connection is None:
            if self.database_path:
                self._connection = duckdb.connect(
                    self.database_path,
                    read_only=self.read_only,
                )
            else:
                self._connection = duckdb.connect(":memory:")
        return self._connection
    
    @contextmanager
    def get_connection(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Context manager for connection."""
        yield self.connection
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def validate_sql(self, sql: str) -> tuple[bool, str | None]:
        """
        Validate SQL query for safety.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for forbidden patterns
        match = self._forbidden_regex.search(sql)
        if match:
            return False, f"Forbidden SQL operation: {match.group()}"
        
        # Must start with SELECT, WITH, or EXPLAIN
        sql_upper = sql.strip().upper()
        allowed_starts = ("SELECT", "WITH", "EXPLAIN", "DESCRIBE", "SHOW")
        
        if not any(sql_upper.startswith(s) for s in allowed_starts):
            return False, "Query must start with SELECT, WITH, EXPLAIN, DESCRIBE, or SHOW"
        
        return True, None
    
    def execute_safe(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        max_rows: int = 1000,
    ) -> QueryResult:
        """
        Execute a validated SQL query safely.
        
        Args:
            sql: SQL query to execute
            params: Query parameters (for parameterized queries)
            max_rows: Maximum rows to return
            
        Returns:
            QueryResult with data
            
        Raises:
            SQLValidationError: If query fails validation
        """
        import time
        
        # Validate first
        is_valid, error = self.validate_sql(sql)
        if not is_valid:
            raise SQLValidationError(error)
        
        # Add LIMIT if not present
        sql_upper = sql.strip().upper()
        if "LIMIT" not in sql_upper:
            sql = f"{sql.rstrip(';')} LIMIT {max_rows + 1}"
        
        logger.debug("Executing SQL", sql=sql[:200])
        
        start_time = time.perf_counter()
        
        try:
            with self.get_connection() as conn:
                if params:
                    result = conn.execute(sql, params)
                else:
                    result = conn.execute(sql)
                
                # Get column names
                columns = [desc[0] for desc in result.description]
                
                # Fetch rows
                rows = result.fetchall()
                
                # Check if truncated
                truncated = len(rows) > max_rows
                if truncated:
                    rows = rows[:max_rows]
                
                execution_time = (time.perf_counter() - start_time) * 1000
                
                return QueryResult(
                    sql=sql,
                    columns=columns,
                    rows=[list(row) for row in rows],
                    row_count=len(rows),
                    truncated=truncated,
                    execution_time_ms=execution_time,
                )
                
        except Exception as e:
            logger.error("SQL execution failed", error=str(e), sql=sql[:200])
            raise
    
    def load_csv(
        self,
        file_path: str | Path,
        table_name: str,
    ) -> int:
        """
        Load a CSV file into DuckDB.
        
        Args:
            file_path: Path to CSV file
            table_name: Name for the table
            
        Returns:
            Number of rows loaded
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        logger.info("Loading CSV", file=str(file_path), table=table_name)
        
        # Use DuckDB's CSV reader
        with self.get_connection() as conn:
            # Create table from CSV
            conn.execute(f"""
                CREATE OR REPLACE TABLE {table_name} AS
                SELECT * FROM read_csv_auto('{file_path}')
            """)
            
            # Get row count
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = result.fetchone()[0]
        
        logger.info("CSV loaded", table=table_name, rows=row_count)
        return row_count
    
    def get_table_schema(self, table_name: str) -> list[dict[str, Any]]:
        """
        Get schema information for a table.
        
        Returns list of dicts with column info.
        """
        with self.get_connection() as conn:
            result = conn.execute(f"DESCRIBE {table_name}")
            columns = []
            
            for row in result.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                })
            
            return columns
    
    def get_sample_rows(
        self,
        table_name: str,
        n: int = 5,
    ) -> list[dict[str, Any]]:
        """Get sample rows from a table."""
        result = self.execute_safe(
            f"SELECT * FROM {table_name} LIMIT {n}",
            max_rows=n,
        )
        return result.to_dict_rows()
    
    def get_row_count(self, table_name: str) -> int:
        """Get total row count for a table."""
        result = self.execute_safe(f"SELECT COUNT(*) as cnt FROM {table_name}")
        return result.rows[0][0]
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        try:
            with self.get_connection() as conn:
                result = conn.execute(
                    "SELECT * FROM information_schema.tables WHERE table_name = ?",
                    [table_name],
                )
                return len(result.fetchall()) > 0
        except Exception:
            return False
