"""
Schema inference for datasets.

Automatically detects:
- Column data types
- Null percentages
- Basic statistics
- Sample values
"""

from typing import Any

import duckdb

from omniagent.config.logging import get_logger
from omniagent.models.dataset import ColumnInfo, ColumnType

logger = get_logger(__name__)


class SchemaInferrer:
    """
    Infers schema and statistics from datasets.
    
    Works with DuckDB tables to extract column information
    and basic statistics.
    """
    
    # Map DuckDB types to our types
    TYPE_MAPPING = {
        "BIGINT": ColumnType.INTEGER,
        "INTEGER": ColumnType.INTEGER,
        "SMALLINT": ColumnType.INTEGER,
        "TINYINT": ColumnType.INTEGER,
        "UBIGINT": ColumnType.INTEGER,
        "UINTEGER": ColumnType.INTEGER,
        "USMALLINT": ColumnType.INTEGER,
        "UTINYINT": ColumnType.INTEGER,
        "HUGEINT": ColumnType.INTEGER,
        "DOUBLE": ColumnType.FLOAT,
        "FLOAT": ColumnType.FLOAT,
        "REAL": ColumnType.FLOAT,
        "DECIMAL": ColumnType.FLOAT,
        "VARCHAR": ColumnType.STRING,
        "CHAR": ColumnType.STRING,
        "TEXT": ColumnType.STRING,
        "STRING": ColumnType.STRING,
        "BOOLEAN": ColumnType.BOOLEAN,
        "BOOL": ColumnType.BOOLEAN,
        "DATE": ColumnType.DATE,
        "TIMESTAMP": ColumnType.DATETIME,
        "TIMESTAMP WITH TIME ZONE": ColumnType.DATETIME,
        "TIME": ColumnType.DATETIME,
    }
    
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        """
        Initialize with a DuckDB connection.
        
        Args:
            connection: Active DuckDB connection
        """
        self.conn = connection
    
    def _map_type(self, duckdb_type: str) -> ColumnType:
        """Map DuckDB type to our column type."""
        # Handle parameterized types like DECIMAL(10,2)
        base_type = duckdb_type.split("(")[0].upper()
        return self.TYPE_MAPPING.get(base_type, ColumnType.UNKNOWN)
    
    def infer_column(
        self,
        table_name: str,
        column_name: str,
        total_rows: int,
    ) -> ColumnInfo:
        """
        Infer detailed information about a single column.
        
        Args:
            table_name: Name of the table
            column_name: Name of the column
            total_rows: Total row count in table
            
        Returns:
            ColumnInfo with all details
        """
        # Get column type
        result = self.conn.execute(f"""
            SELECT typeof("{column_name}")
            FROM {table_name}
            WHERE "{column_name}" IS NOT NULL
            LIMIT 1
        """)
        row = result.fetchone()
        raw_type = row[0] if row else "UNKNOWN"
        dtype = self._map_type(raw_type)
        
        # Get null count
        result = self.conn.execute(f"""
            SELECT 
                COUNT(*) FILTER (WHERE "{column_name}" IS NULL) as null_count,
                COUNT(DISTINCT "{column_name}") as unique_count
            FROM {table_name}
        """)
        row = result.fetchone()
        null_count = row[0]
        unique_count = row[1]
        
        null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
        
        # Get sample values
        result = self.conn.execute(f"""
            SELECT DISTINCT "{column_name}"
            FROM {table_name}
            WHERE "{column_name}" IS NOT NULL
            LIMIT 5
        """)
        sample_values = [row[0] for row in result.fetchall()]
        
        # Build column info
        column_info = ColumnInfo(
            name=column_name,
            dtype=dtype,
            nullable=null_count > 0,
            null_count=null_count,
            null_percentage=round(null_percentage, 2),
            unique_count=unique_count,
            sample_values=sample_values,
        )
        
        # Add numeric stats if applicable
        if dtype in (ColumnType.INTEGER, ColumnType.FLOAT):
            column_info = self._add_numeric_stats(
                table_name, column_name, column_info
            )
        
        # Add categorical stats if string type
        if dtype == ColumnType.STRING:
            column_info = self._add_categorical_stats(
                table_name, column_name, column_info
            )
        
        return column_info
    
    def _add_numeric_stats(
        self,
        table_name: str,
        column_name: str,
        column_info: ColumnInfo,
    ) -> ColumnInfo:
        """Add numeric statistics to column info."""
        try:
            result = self.conn.execute(f"""
                SELECT
                    MIN("{column_name}") as min_val,
                    MAX("{column_name}") as max_val,
                    AVG("{column_name}") as mean_val,
                    MEDIAN("{column_name}") as median_val,
                    STDDEV("{column_name}") as std_val
                FROM {table_name}
                WHERE "{column_name}" IS NOT NULL
            """)
            row = result.fetchone()
            
            if row:
                column_info.min_value = float(row[0]) if row[0] is not None else None
                column_info.max_value = float(row[1]) if row[1] is not None else None
                column_info.mean_value = float(row[2]) if row[2] is not None else None
                column_info.median_value = float(row[3]) if row[3] is not None else None
                column_info.std_value = float(row[4]) if row[4] is not None else None
                
        except Exception as e:
            logger.warning(f"Could not compute numeric stats for {column_name}: {e}")
        
        return column_info
    
    def _add_categorical_stats(
        self,
        table_name: str,
        column_name: str,
        column_info: ColumnInfo,
    ) -> ColumnInfo:
        """Add categorical statistics to column info."""
        try:
            result = self.conn.execute(f"""
                SELECT "{column_name}" as value, COUNT(*) as count
                FROM {table_name}
                WHERE "{column_name}" IS NOT NULL
                GROUP BY "{column_name}"
                ORDER BY count DESC
                LIMIT 10
            """)
            
            top_values = [
                {"value": row[0], "count": row[1]}
                for row in result.fetchall()
            ]
            column_info.top_values = top_values
            
        except Exception as e:
            logger.warning(f"Could not compute categorical stats for {column_name}: {e}")
        
        return column_info
    
    def infer_all_columns(
        self,
        table_name: str,
    ) -> list[ColumnInfo]:
        """
        Infer information for all columns in a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of ColumnInfo for all columns
        """
        # Get column names
        result = self.conn.execute(f"DESCRIBE {table_name}")
        columns_raw = [(row[0], row[1]) for row in result.fetchall()]
        
        # Get total row count
        result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = result.fetchone()[0]
        
        logger.info(
            "Inferring schema",
            table=table_name,
            columns=len(columns_raw),
            rows=total_rows,
        )
        
        # Infer each column
        columns = []
        for col_name, col_type in columns_raw:
            col_info = self.infer_column(table_name, col_name, total_rows)
            columns.append(col_info)
        
        return columns
