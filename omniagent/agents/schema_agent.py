"""
Schema Agent - Dataset structure and metadata tools.

Provides tools for:
- Getting column information
- Understanding data types
- Sampling data
"""

from typing import Any

from omniagent.agents.base import BaseAgent
from omniagent.mcp.server import mcp_tool


class SchemaAgent(BaseAgent):
    """
    Agent for dataset schema and structure operations.
    
    Tools:
    - get_columns: List all columns with types
    - get_sample: Get sample rows
    - get_column_info: Detailed info about a column
    """
    
    name = "schema_agent"
    description = "Provides dataset structure and metadata information"
    
    @mcp_tool
    def get_columns(self) -> dict[str, Any]:
        """
        Get all columns in the dataset with their types.
        
        Returns:
            Dictionary with columns list containing name and type for each
        """
        table_name = self._get_table_name()
        result = self.db.connection.execute(f"DESCRIBE {table_name}")
        
        columns = [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
            }
            for row in result.fetchall()
        ]
        
        return {
            "table": table_name,
            "column_count": len(columns),
            "columns": columns,
        }
    
    @mcp_tool
    def get_sample(self, n: int = 5) -> dict[str, Any]:
        """
        Get sample rows from the dataset.
        
        Args:
            n: Number of rows to return (default 5, max 100)
            
        Returns:
            Dictionary with columns and sample rows
        """
        n = min(max(1, n), 100)  # Clamp between 1 and 100
        table_name = self._get_table_name()
        
        result = self.db.execute_safe(
            f"SELECT * FROM {table_name} LIMIT {n}",
            max_rows=n,
        )
        
        return {
            "table": table_name,
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
        }
    
    @mcp_tool
    def get_column_info(self, column: str) -> dict[str, Any]:
        """
        Get detailed information about a specific column.
        
        Args:
            column: Name of the column to inspect
            
        Returns:
            Dictionary with column statistics and sample values
        """
        table_name = self._get_table_name()
        
        # Validate column exists
        valid, error = self._validate_columns(table_name, [column])
        if not valid:
            return {"error": error}
        
        # Get basic stats
        result = self.db.connection.execute(f"""
            SELECT
                COUNT(*) as total_count,
                COUNT("{column}") as non_null_count,
                COUNT(DISTINCT "{column}") as unique_count
            FROM {table_name}
        """)
        row = result.fetchone()
        
        info: dict[str, Any] = {
            "column": column,
            "total_count": row[0],
            "non_null_count": row[1],
            "null_count": row[0] - row[1],
            "null_percentage": round((row[0] - row[1]) / row[0] * 100, 2) if row[0] > 0 else 0,
            "unique_count": row[2],
        }
        
        # Check if numeric
        if column in self._get_numeric_columns(table_name):
            result = self.db.connection.execute(f"""
                SELECT
                    MIN("{column}") as min_val,
                    MAX("{column}") as max_val,
                    AVG("{column}") as mean_val,
                    MEDIAN("{column}") as median_val
                FROM {table_name}
                WHERE "{column}" IS NOT NULL
            """)
            stats = result.fetchone()
            info["numeric_stats"] = {
                "min": stats[0],
                "max": stats[1],
                "mean": round(stats[2], 4) if stats[2] else None,
                "median": stats[3],
            }
        else:
            # Get top values for categorical
            result = self.db.connection.execute(f"""
                SELECT "{column}" as value, COUNT(*) as count
                FROM {table_name}
                WHERE "{column}" IS NOT NULL
                GROUP BY "{column}"
                ORDER BY count DESC
                LIMIT 10
            """)
            info["top_values"] = [
                {"value": row[0], "count": row[1]}
                for row in result.fetchall()
            ]
        
        # Get sample values
        result = self.db.connection.execute(f"""
            SELECT DISTINCT "{column}"
            FROM {table_name}
            WHERE "{column}" IS NOT NULL
            LIMIT 5
        """)
        info["sample_values"] = [row[0] for row in result.fetchall()]
        
        return info
    
    @mcp_tool
    def get_row_count(self) -> dict[str, Any]:
        """
        Get the total number of rows in the dataset.
        
        Returns:
            Dictionary with table name and row count
        """
        table_name = self._get_table_name()
        result = self.db.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = result.fetchone()[0]
        
        return {
            "table": table_name,
            "row_count": count,
        }
