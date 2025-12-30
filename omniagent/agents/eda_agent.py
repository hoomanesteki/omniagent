"""
EDA Agent - Exploratory Data Analysis tools.

Provides tools for:
- Dataset profiling
- Missing value analysis
- Outlier detection
"""

from typing import Any

from omniagent.agents.base import BaseAgent
from omniagent.mcp.server import mcp_tool


class EDAAgent(BaseAgent):
    """
    Agent for exploratory data analysis.
    
    Tools:
    - profile: Complete dataset profile
    - missing_report: Analysis of missing values
    - outlier_detect: Find outliers in numeric columns
    - value_counts: Get value frequencies
    """
    
    name = "eda_agent"
    description = "Performs exploratory data analysis on the dataset"
    
    @mcp_tool
    def profile(self) -> dict[str, Any]:
        """
        Generate a complete profile of the dataset.
        
        Returns:
            Dictionary with dataset overview, column stats, and quality metrics
        """
        table_name = self._get_table_name()
        
        # Get row count
        result = self.db.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = result.fetchone()[0]
        
        # Get column info
        result = self.db.connection.execute(f"DESCRIBE {table_name}")
        columns_raw = [(row[0], row[1]) for row in result.fetchall()]
        
        columns = []
        total_nulls = 0
        
        for col_name, col_type in columns_raw:
            # Get null count
            null_result = self.db.connection.execute(f"""
                SELECT 
                    COUNT(*) FILTER (WHERE "{col_name}" IS NULL) as null_count,
                    COUNT(DISTINCT "{col_name}") as unique_count
                FROM {table_name}
            """)
            null_row = null_result.fetchone()
            null_count = null_row[0]
            unique_count = null_row[1]
            total_nulls += null_count
            
            col_info: dict[str, Any] = {
                "name": col_name,
                "type": col_type,
                "null_count": null_count,
                "null_percentage": round(null_count / row_count * 100, 2) if row_count > 0 else 0,
                "unique_count": unique_count,
            }
            columns.append(col_info)
        
        total_cells = row_count * len(columns_raw)
        
        return {
            "table": table_name,
            "row_count": row_count,
            "column_count": len(columns_raw),
            "total_cells": total_cells,
            "total_null_cells": total_nulls,
            "null_percentage": round(total_nulls / total_cells * 100, 2) if total_cells > 0 else 0,
            "columns": columns,
            "numeric_columns": self._get_numeric_columns(table_name),
            "categorical_columns": self._get_categorical_columns(table_name),
        }
    
    @mcp_tool
    def missing_report(self) -> dict[str, Any]:
        """
        Generate a detailed report of missing values.
        
        Returns:
            Dictionary with missing value statistics per column
        """
        table_name = self._get_table_name()
        
        # Get row count
        result = self.db.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = result.fetchone()[0]
        
        # Get column names
        result = self.db.connection.execute(f"DESCRIBE {table_name}")
        columns = [row[0] for row in result.fetchall()]
        
        missing_data = []
        
        for col in columns:
            result = self.db.connection.execute(f"""
                SELECT COUNT(*) FILTER (WHERE "{col}" IS NULL)
                FROM {table_name}
            """)
            null_count = result.fetchone()[0]
            
            if null_count > 0:
                missing_data.append({
                    "column": col,
                    "missing_count": null_count,
                    "missing_percentage": round(null_count / row_count * 100, 2),
                    "present_count": row_count - null_count,
                })
        
        # Sort by missing percentage descending
        missing_data.sort(key=lambda x: x["missing_percentage"], reverse=True)
        
        return {
            "table": table_name,
            "row_count": row_count,
            "columns_with_missing": len(missing_data),
            "total_columns": len(columns),
            "missing_data": missing_data,
        }
    
    @mcp_tool
    def outlier_detect(
        self,
        column: str,
        method: str = "iqr",
    ) -> dict[str, Any]:
        """
        Detect outliers in a numeric column.
        
        Args:
            column: Name of the numeric column
            method: Detection method - 'iqr' (default) or 'zscore'
            
        Returns:
            Dictionary with outlier statistics and values
        """
        table_name = self._get_table_name()
        
        # Validate column
        valid, error = self._validate_columns(table_name, [column])
        if not valid:
            return {"error": error}
        
        # Check if numeric
        if column not in self._get_numeric_columns(table_name):
            return {"error": f"Column '{column}' is not numeric"}
        
        if method == "iqr":
            # IQR method: outliers are < Q1 - 1.5*IQR or > Q3 + 1.5*IQR
            result = self.db.connection.execute(f"""
                WITH stats AS (
                    SELECT
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "{column}") as q1,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY "{column}") as q3
                    FROM {table_name}
                    WHERE "{column}" IS NOT NULL
                )
                SELECT 
                    q1,
                    q3,
                    q3 - q1 as iqr,
                    q1 - 1.5 * (q3 - q1) as lower_bound,
                    q3 + 1.5 * (q3 - q1) as upper_bound
                FROM stats
            """)
            stats = result.fetchone()
            q1, q3, iqr, lower_bound, upper_bound = stats
            
            # Count outliers
            result = self.db.connection.execute(f"""
                SELECT 
                    COUNT(*) FILTER (WHERE "{column}" < {lower_bound}) as lower_outliers,
                    COUNT(*) FILTER (WHERE "{column}" > {upper_bound}) as upper_outliers,
                    COUNT(*) as total_non_null
                FROM {table_name}
                WHERE "{column}" IS NOT NULL
            """)
            counts = result.fetchone()
            
            # Get some outlier values
            result = self.db.connection.execute(f"""
                SELECT "{column}"
                FROM {table_name}
                WHERE "{column}" IS NOT NULL
                  AND ("{column}" < {lower_bound} OR "{column}" > {upper_bound})
                LIMIT 20
            """)
            outlier_values = [row[0] for row in result.fetchall()]
            
            return {
                "column": column,
                "method": "iqr",
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "lower_outlier_count": counts[0],
                "upper_outlier_count": counts[1],
                "total_outliers": counts[0] + counts[1],
                "total_values": counts[2],
                "outlier_percentage": round((counts[0] + counts[1]) / counts[2] * 100, 2) if counts[2] > 0 else 0,
                "sample_outliers": outlier_values[:10],
            }
        
        elif method == "zscore":
            # Z-score method: outliers have |z| > 3
            result = self.db.connection.execute(f"""
                WITH stats AS (
                    SELECT
                        AVG("{column}") as mean,
                        STDDEV("{column}") as std
                    FROM {table_name}
                    WHERE "{column}" IS NOT NULL
                )
                SELECT mean, std FROM stats
            """)
            mean, std = result.fetchone()
            
            if std == 0 or std is None:
                return {
                    "column": column,
                    "method": "zscore",
                    "error": "Cannot compute z-scores: standard deviation is zero",
                }
            
            # Count outliers
            result = self.db.connection.execute(f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE "{column}" IS NOT NULL
                  AND ABS(("{column}" - {mean}) / {std}) > 3
            """)
            outlier_count = result.fetchone()[0]
            
            result = self.db.connection.execute(f"""
                SELECT COUNT(*) FROM {table_name} WHERE "{column}" IS NOT NULL
            """)
            total_count = result.fetchone()[0]
            
            return {
                "column": column,
                "method": "zscore",
                "mean": mean,
                "std": std,
                "threshold": 3,
                "outlier_count": outlier_count,
                "total_values": total_count,
                "outlier_percentage": round(outlier_count / total_count * 100, 2) if total_count > 0 else 0,
            }
        
        else:
            return {"error": f"Unknown method: {method}. Use 'iqr' or 'zscore'"}
    
    @mcp_tool
    def value_counts(
        self,
        column: str,
        top_n: int = 20,
    ) -> dict[str, Any]:
        """
        Get value frequencies for a column.
        
        Args:
            column: Name of the column
            top_n: Number of top values to return (default 20)
            
        Returns:
            Dictionary with value counts
        """
        table_name = self._get_table_name()
        
        # Validate column
        valid, error = self._validate_columns(table_name, [column])
        if not valid:
            return {"error": error}
        
        top_n = min(max(1, top_n), 100)
        
        result = self.db.connection.execute(f"""
            SELECT 
                "{column}" as value,
                COUNT(*) as count
            FROM {table_name}
            GROUP BY "{column}"
            ORDER BY count DESC
            LIMIT {top_n}
        """)
        
        values = [
            {"value": row[0], "count": row[1]}
            for row in result.fetchall()
        ]
        
        # Get total unique count
        result = self.db.connection.execute(f"""
            SELECT COUNT(DISTINCT "{column}") FROM {table_name}
        """)
        unique_count = result.fetchone()[0]
        
        return {
            "column": column,
            "unique_count": unique_count,
            "showing_top": min(top_n, len(values)),
            "values": values,
        }
