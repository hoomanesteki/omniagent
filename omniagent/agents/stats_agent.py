"""
Stats Agent - Statistical computation tools.

Provides tools for:
- Descriptive statistics
- Correlation analysis
- Aggregations and groupby
"""

from typing import Any

from omniagent.agents.base import BaseAgent
from omniagent.mcp.server import mcp_tool


class StatsAgent(BaseAgent):
    """
    Agent for statistical computations.
    
    Tools:
    - describe: Descriptive statistics for columns
    - correlate: Correlation matrix
    - aggregate: Aggregation operations
    - groupby: Group-by analysis
    """
    
    name = "stats_agent"
    description = "Performs statistical computations on the dataset"
    
    @mcp_tool
    def describe(
        self,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compute descriptive statistics for numeric columns.
        
        Args:
            columns: List of columns to describe. None for all numeric columns.
            
        Returns:
            Dictionary with statistics for each column
        """
        table_name = self._get_table_name()
        
        # Get numeric columns if not specified
        if columns is None:
            columns = self._get_numeric_columns(table_name)
        else:
            # Validate columns
            valid, error = self._validate_columns(table_name, columns)
            if not valid:
                return {"error": error}
            # Filter to numeric only
            numeric_cols = self._get_numeric_columns(table_name)
            columns = [c for c in columns if c in numeric_cols]
        
        if not columns:
            return {"error": "No numeric columns to describe"}
        
        stats = []
        
        for col in columns:
            result = self.db.connection.execute(f"""
                SELECT
                    COUNT("{col}") as count,
                    AVG("{col}") as mean,
                    STDDEV("{col}") as std,
                    MIN("{col}") as min,
                    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{col}") as q25,
                    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY "{col}") as median,
                    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{col}") as q75,
                    MAX("{col}") as max
                FROM {table_name}
                WHERE "{col}" IS NOT NULL
            """)
            row = result.fetchone()
            
            stats.append({
                "column": col,
                "count": row[0],
                "mean": round(row[1], 4) if row[1] else None,
                "std": round(row[2], 4) if row[2] else None,
                "min": row[3],
                "25%": row[4],
                "50%": row[5],
                "75%": row[6],
                "max": row[7],
            })
        
        return {
            "table": table_name,
            "statistics": stats,
        }
    
    @mcp_tool
    def correlate(
        self,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compute correlation matrix for numeric columns.
        
        Args:
            columns: List of columns to correlate. None for all numeric columns.
            
        Returns:
            Dictionary with correlation matrix
        """
        table_name = self._get_table_name()
        
        # Get numeric columns if not specified
        if columns is None:
            columns = self._get_numeric_columns(table_name)
        else:
            # Validate and filter
            valid, error = self._validate_columns(table_name, columns)
            if not valid:
                return {"error": error}
            numeric_cols = self._get_numeric_columns(table_name)
            columns = [c for c in columns if c in numeric_cols]
        
        if len(columns) < 2:
            return {"error": "Need at least 2 numeric columns for correlation"}
        
        # Build correlation matrix
        matrix = []
        
        for col1 in columns:
            row = []
            for col2 in columns:
                if col1 == col2:
                    row.append(1.0)
                else:
                    result = self.db.connection.execute(f"""
                        SELECT CORR("{col1}", "{col2}")
                        FROM {table_name}
                        WHERE "{col1}" IS NOT NULL AND "{col2}" IS NOT NULL
                    """)
                    corr = result.fetchone()[0]
                    row.append(round(corr, 4) if corr else None)
            matrix.append(row)
        
        # Find top correlations (excluding self-correlation)
        top_correlations = []
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i < j and matrix[i][j] is not None:
                    top_correlations.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": matrix[i][j],
                    })
        
        # Sort by absolute correlation
        top_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return {
            "table": table_name,
            "columns": columns,
            "matrix": matrix,
            "top_correlations": top_correlations[:10],
        }
    
    @mcp_tool
    def aggregate(
        self,
        column: str,
        operation: str,
    ) -> dict[str, Any]:
        """
        Perform an aggregation operation on a column.
        
        Args:
            column: Column to aggregate
            operation: Operation - 'sum', 'avg', 'min', 'max', 'count', 'std'
            
        Returns:
            Dictionary with aggregation result
        """
        table_name = self._get_table_name()
        
        # Validate column
        valid, error = self._validate_columns(table_name, [column])
        if not valid:
            return {"error": error}
        
        # Map operation to SQL
        op_map = {
            "sum": "SUM",
            "avg": "AVG",
            "mean": "AVG",
            "min": "MIN",
            "max": "MAX",
            "count": "COUNT",
            "std": "STDDEV",
            "stddev": "STDDEV",
            "var": "VARIANCE",
            "variance": "VARIANCE",
        }
        
        sql_op = op_map.get(operation.lower())
        if not sql_op:
            return {"error": f"Unknown operation: {operation}. Use: {', '.join(op_map.keys())}"}
        
        result = self.db.connection.execute(f"""
            SELECT {sql_op}("{column}")
            FROM {table_name}
        """)
        value = result.fetchone()[0]
        
        return {
            "column": column,
            "operation": operation,
            "result": round(value, 4) if isinstance(value, float) else value,
        }
    
    @mcp_tool
    def groupby(
        self,
        group_column: str,
        agg_column: str,
        operation: str = "avg",
        top_n: int = 20,
    ) -> dict[str, Any]:
        """
        Perform group-by aggregation.
        
        Args:
            group_column: Column to group by
            agg_column: Column to aggregate
            operation: Aggregation operation (sum, avg, min, max, count)
            top_n: Number of groups to return (default 20)
            
        Returns:
            Dictionary with grouped results
        """
        table_name = self._get_table_name()
        
        # Validate columns
        valid, error = self._validate_columns(table_name, [group_column, agg_column])
        if not valid:
            return {"error": error}
        
        # Map operation
        op_map = {
            "sum": "SUM",
            "avg": "AVG",
            "mean": "AVG",
            "min": "MIN",
            "max": "MAX",
            "count": "COUNT",
        }
        
        sql_op = op_map.get(operation.lower())
        if not sql_op:
            return {"error": f"Unknown operation: {operation}"}
        
        top_n = min(max(1, top_n), 100)
        
        result = self.db.connection.execute(f"""
            SELECT 
                "{group_column}" as group_value,
                {sql_op}("{agg_column}") as agg_value,
                COUNT(*) as group_count
            FROM {table_name}
            GROUP BY "{group_column}"
            ORDER BY agg_value DESC
            LIMIT {top_n}
        """)
        
        groups = [
            {
                "group": row[0],
                "value": round(row[1], 4) if isinstance(row[1], float) else row[1],
                "count": row[2],
            }
            for row in result.fetchall()
        ]
        
        return {
            "group_column": group_column,
            "agg_column": agg_column,
            "operation": operation,
            "groups": groups,
        }
    
    @mcp_tool
    def percentile(
        self,
        column: str,
        percentiles: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate percentiles for a numeric column.
        
        Args:
            column: Column to analyze
            percentiles: List of percentiles (0-100). Default: [10, 25, 50, 75, 90]
            
        Returns:
            Dictionary with percentile values
        """
        table_name = self._get_table_name()
        
        # Validate column
        valid, error = self._validate_columns(table_name, [column])
        if not valid:
            return {"error": error}
        
        if column not in self._get_numeric_columns(table_name):
            return {"error": f"Column '{column}' is not numeric"}
        
        if percentiles is None:
            percentiles = [10, 25, 50, 75, 90]
        
        # Validate percentiles
        percentiles = [p for p in percentiles if 0 <= p <= 100]
        
        results = {}
        for p in percentiles:
            result = self.db.connection.execute(f"""
                SELECT PERCENTILE_CONT({p / 100}) WITHIN GROUP (ORDER BY "{column}")
                FROM {table_name}
                WHERE "{column}" IS NOT NULL
            """)
            value = result.fetchone()[0]
            results[f"p{int(p)}"] = value
        
        return {
            "column": column,
            "percentiles": results,
        }
