"""
SQL Agent - Safe SQL query execution.

Provides tools for:
- Executing SELECT queries
- Query validation
- Query explanation
"""

from typing import Any

from omniagent.agents.base import BaseAgent
from omniagent.data.duckdb_engine import SQLValidationError
from omniagent.mcp.server import mcp_tool


class SQLAgent(BaseAgent):
    """
    Agent for safe SQL query execution.
    
    All queries are validated to be SELECT-only.
    No DDL or DML operations are allowed.
    
    Tools:
    - query: Execute a SELECT query
    - validate_sql: Check if a query is valid
    - explain_query: Get query execution plan
    """
    
    name = "sql_agent"
    description = "Executes safe read-only SQL queries on the dataset"
    
    @mcp_tool
    def query(
        self,
        sql: str,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Execute a SELECT query on the dataset.
        
        Args:
            sql: The SQL query to execute (SELECT only)
            limit: Maximum rows to return (default 100, max 1000)
            
        Returns:
            Dictionary with columns, rows, and metadata
        """
        limit = min(max(1, limit), 1000)
        
        try:
            result = self.db.execute_safe(sql, max_rows=limit)
            
            return {
                "success": True,
                "sql": result.sql,
                "columns": result.columns,
                "rows": result.rows,
                "row_count": result.row_count,
                "truncated": result.truncated,
                "execution_time_ms": round(result.execution_time_ms or 0, 2),
            }
            
        except SQLValidationError as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "validation_error",
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": "execution_error",
            }
    
    @mcp_tool
    def validate_sql(self, sql: str) -> dict[str, Any]:
        """
        Validate a SQL query without executing it.
        
        Args:
            sql: The SQL query to validate
            
        Returns:
            Dictionary indicating if query is valid and safe
        """
        is_valid, error = self.db.validate_sql(sql)
        
        result: dict[str, Any] = {
            "sql": sql,
            "is_valid": is_valid,
        }
        
        if not is_valid:
            result["error"] = error
        
        # Try to parse to check syntax
        if is_valid:
            try:
                self.db.connection.execute(f"EXPLAIN {sql}")
                result["syntax_valid"] = True
            except Exception as e:
                result["syntax_valid"] = False
                result["syntax_error"] = str(e)
        
        return result
    
    @mcp_tool
    def explain_query(self, sql: str) -> dict[str, Any]:
        """
        Get the execution plan for a query.
        
        Args:
            sql: The SQL query to explain
            
        Returns:
            Dictionary with the query execution plan
        """
        # First validate
        is_valid, error = self.db.validate_sql(sql)
        if not is_valid:
            return {
                "success": False,
                "error": error,
            }
        
        try:
            result = self.db.connection.execute(f"EXPLAIN {sql}")
            plan = result.fetchall()
            
            return {
                "success": True,
                "sql": sql,
                "plan": [row[0] if len(row) == 1 else row for row in plan],
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    @mcp_tool
    def get_table_info(self) -> dict[str, Any]:
        """
        Get information about available tables.
        
        Returns:
            Dictionary with list of tables and their schemas
        """
        result = self.db.connection.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
        """)
        
        tables = []
        for row in result.fetchall():
            table_name = row[0]
            
            # Get column info
            col_result = self.db.connection.execute(f"DESCRIBE {table_name}")
            columns = [
                {"name": r[0], "type": r[1]}
                for r in col_result.fetchall()
            ]
            
            # Get row count
            count_result = self.db.connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            )
            row_count = count_result.fetchone()[0]
            
            tables.append({
                "name": table_name,
                "columns": columns,
                "row_count": row_count,
            })
        
        return {
            "tables": tables,
            "table_count": len(tables),
        }
