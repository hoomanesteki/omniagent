"""
Dataset-related data models.

These models represent:
- Column information (name, type, stats)
- Dataset metadata (file info, schema)
- Dataset profile (comprehensive summary)
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ColumnType(str, Enum):
    """Inferred column data types."""
    
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    UNKNOWN = "unknown"


class ColumnInfo(BaseModel):
    """Information about a single column."""
    
    name: str = Field(description="Column name")
    dtype: ColumnType = Field(description="Inferred data type")
    nullable: bool = Field(description="Whether column has null values")
    null_count: int = Field(default=0, description="Number of null values")
    null_percentage: float = Field(default=0.0, description="Percentage of nulls")
    unique_count: int = Field(default=0, description="Number of unique values")
    sample_values: list[Any] = Field(
        default_factory=list,
        description="Sample of values from this column",
    )
    
    # Numeric column stats (optional)
    min_value: float | None = Field(default=None, description="Minimum value")
    max_value: float | None = Field(default=None, description="Maximum value")
    mean_value: float | None = Field(default=None, description="Mean value")
    median_value: float | None = Field(default=None, description="Median value")
    std_value: float | None = Field(default=None, description="Standard deviation")
    
    # Categorical column stats (optional)
    top_values: list[dict[str, Any]] | None = Field(
        default=None,
        description="Most frequent values with counts",
    )


class DatasetMetadata(BaseModel):
    """Basic metadata about an uploaded dataset."""
    
    dataset_id: str = Field(description="Unique identifier for this dataset")
    filename: str = Field(description="Original filename")
    file_size_bytes: int = Field(description="File size in bytes")
    uploaded_at: datetime = Field(default_factory=datetime.now)
    
    # Schema info
    row_count: int = Field(description="Total number of rows")
    column_count: int = Field(description="Total number of columns")
    columns: list[ColumnInfo] = Field(
        default_factory=list,
        description="Column information",
    )
    
    # Storage info
    storage_path: str = Field(description="Path to stored file")
    table_name: str = Field(description="DuckDB table name")
    
    @property
    def column_names(self) -> list[str]:
        """Get list of column names."""
        return [col.name for col in self.columns]
    
    @property
    def numeric_columns(self) -> list[str]:
        """Get list of numeric column names."""
        return [
            col.name
            for col in self.columns
            if col.dtype in (ColumnType.INTEGER, ColumnType.FLOAT)
        ]
    
    @property
    def categorical_columns(self) -> list[str]:
        """Get list of categorical column names."""
        return [
            col.name
            for col in self.columns
            if col.dtype == ColumnType.STRING
        ]


class DatasetProfile(BaseModel):
    """
    Comprehensive profile of a dataset.
    
    This is generated after upload and provides
    a full summary for the Master Agent to use.
    """
    
    metadata: DatasetMetadata = Field(description="Basic dataset metadata")
    
    # Quality metrics
    total_null_cells: int = Field(default=0, description="Total null cells")
    null_percentage: float = Field(default=0.0, description="Overall null %")
    duplicate_row_count: int = Field(default=0, description="Duplicate rows")
    
    # Summary statistics
    memory_usage_mb: float = Field(default=0.0, description="Memory usage")
    
    # Sample data
    sample_rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Sample of data rows",
    )
    
    def to_context_string(self) -> str:
        """
        Generate a string summary for LLM context.
        
        This is what the Master Agent will see about the dataset.
        """
        lines = [
            f"Dataset: {self.metadata.filename}",
            f"Rows: {self.metadata.row_count:,}",
            f"Columns: {self.metadata.column_count}",
            "",
            "Columns:",
        ]
        
        for col in self.metadata.columns:
            type_str = col.dtype.value
            null_str = f"{col.null_percentage:.1f}% null" if col.nullable else "no nulls"
            lines.append(f"  - {col.name} ({type_str}, {null_str})")
        
        lines.extend([
            "",
            f"Numeric columns: {', '.join(self.metadata.numeric_columns) or 'none'}",
            f"Categorical columns: {', '.join(self.metadata.categorical_columns) or 'none'}",
        ])
        
        return "\n".join(lines)
