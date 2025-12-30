"""
Analysis result data models.

These models represent the outputs from various
analysis operations.
"""

from typing import Any

from pydantic import BaseModel, Field


class QueryResult(BaseModel):
    """Result from a SQL query."""
    
    sql: str = Field(description="Executed SQL query")
    columns: list[str] = Field(description="Column names in result")
    rows: list[list[Any]] = Field(description="Result rows")
    row_count: int = Field(description="Number of rows returned")
    total_row_count: int | None = Field(
        default=None,
        description="Total rows before limit (if truncated)",
    )
    truncated: bool = Field(
        default=False,
        description="Whether result was truncated",
    )
    execution_time_ms: float | None = Field(
        default=None,
        description="Query execution time",
    )
    
    def to_dict_rows(self) -> list[dict[str, Any]]:
        """Convert to list of dictionaries."""
        return [
            dict(zip(self.columns, row))
            for row in self.rows
        ]
    
    def to_markdown_table(self, max_rows: int = 10) -> str:
        """Format as markdown table."""
        if not self.rows:
            return "_No results_"
        
        # Header
        header = "| " + " | ".join(self.columns) + " |"
        separator = "| " + " | ".join(["---"] * len(self.columns)) + " |"
        
        # Rows
        display_rows = self.rows[:max_rows]
        row_lines = []
        for row in display_rows:
            formatted = [str(v) if v is not None else "NULL" for v in row]
            row_lines.append("| " + " | ".join(formatted) + " |")
        
        result = "\n".join([header, separator] + row_lines)
        
        if len(self.rows) > max_rows:
            result += f"\n\n_...and {len(self.rows) - max_rows} more rows_"
        
        return result


class StatsSummary(BaseModel):
    """Summary statistics for a column or dataset."""
    
    column_name: str | None = Field(
        default=None,
        description="Column name (if for single column)",
    )
    
    # Count stats
    count: int = Field(description="Number of non-null values")
    null_count: int = Field(default=0, description="Number of null values")
    unique_count: int = Field(default=0, description="Number of unique values")
    
    # Numeric stats (optional)
    mean: float | None = Field(default=None)
    std: float | None = Field(default=None)
    min: float | None = Field(default=None)
    max: float | None = Field(default=None)
    median: float | None = Field(default=None)
    q25: float | None = Field(default=None, description="25th percentile")
    q75: float | None = Field(default=None, description="75th percentile")
    
    # Categorical stats (optional)
    top_values: list[dict[str, Any]] | None = Field(
        default=None,
        description="Most frequent values",
    )
    
    def to_markdown(self) -> str:
        """Format as markdown."""
        lines = []
        
        if self.column_name:
            lines.append(f"**{self.column_name}**")
        
        lines.append(f"- Count: {self.count:,}")
        
        if self.null_count > 0:
            lines.append(f"- Nulls: {self.null_count:,}")
        
        lines.append(f"- Unique: {self.unique_count:,}")
        
        if self.mean is not None:
            lines.extend([
                f"- Mean: {self.mean:.2f}",
                f"- Std: {self.std:.2f}" if self.std else "",
                f"- Min: {self.min:.2f}" if self.min is not None else "",
                f"- Max: {self.max:.2f}" if self.max is not None else "",
                f"- Median: {self.median:.2f}" if self.median is not None else "",
            ])
        
        if self.top_values:
            lines.append("- Top values:")
            for item in self.top_values[:5]:
                lines.append(f"  - {item['value']}: {item['count']:,}")
        
        return "\n".join(line for line in lines if line)


class CorrelationMatrix(BaseModel):
    """Correlation matrix between numeric columns."""
    
    columns: list[str] = Field(description="Column names")
    matrix: list[list[float]] = Field(description="Correlation values")
    
    def get_correlation(self, col1: str, col2: str) -> float | None:
        """Get correlation between two columns."""
        try:
            i = self.columns.index(col1)
            j = self.columns.index(col2)
            return self.matrix[i][j]
        except (ValueError, IndexError):
            return None
    
    def get_top_correlations(
        self,
        n: int = 10,
        min_abs_corr: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Get top N strongest correlations."""
        pairs = []
        
        for i, col1 in enumerate(self.columns):
            for j, col2 in enumerate(self.columns):
                if i < j:  # Avoid duplicates and self-correlation
                    corr = self.matrix[i][j]
                    if abs(corr) >= min_abs_corr:
                        pairs.append({
                            "column1": col1,
                            "column2": col2,
                            "correlation": round(corr, 4),
                        })
        
        # Sort by absolute correlation
        pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return pairs[:n]
    
    def to_markdown(self) -> str:
        """Format as markdown table."""
        # Header
        header = "| | " + " | ".join(self.columns) + " |"
        separator = "| --- | " + " | ".join(["---"] * len(self.columns)) + " |"
        
        # Rows
        rows = []
        for i, col in enumerate(self.columns):
            values = [f"{v:.2f}" for v in self.matrix[i]]
            rows.append(f"| {col} | " + " | ".join(values) + " |")
        
        return "\n".join([header, separator] + rows)


class RegressionResult(BaseModel):
    """Result from fitting a regression model."""
    
    # Model info
    model_type: str = Field(description="Type of model (linear, ridge, etc.)")
    target_column: str = Field(description="Target variable")
    feature_columns: list[str] = Field(description="Feature variables")
    
    # Metrics
    r2_score: float = Field(description="R² score")
    rmse: float = Field(description="Root Mean Squared Error")
    mae: float = Field(description="Mean Absolute Error")
    
    # Coefficients
    intercept: float = Field(description="Model intercept")
    coefficients: dict[str, float] = Field(
        description="Feature coefficients",
    )
    
    # Optional: detailed diagnostics
    train_size: int | None = Field(default=None)
    test_size: int | None = Field(default=None)
    
    def to_markdown(self) -> str:
        """Format as markdown."""
        lines = [
            f"## Regression Results: {self.target_column}",
            "",
            f"**Model:** {self.model_type}",
            f"**Features:** {', '.join(self.feature_columns)}",
            "",
            "### Metrics",
            f"- R² Score: {self.r2_score:.4f}",
            f"- RMSE: {self.rmse:.4f}",
            f"- MAE: {self.mae:.4f}",
            "",
            "### Coefficients",
            f"- Intercept: {self.intercept:.4f}",
        ]
        
        # Sort coefficients by absolute value
        sorted_coefs = sorted(
            self.coefficients.items(),
            key=lambda x: abs(x[1]),
            reverse=True,
        )
        
        for feature, coef in sorted_coefs:
            lines.append(f"- {feature}: {coef:.4f}")
        
        return "\n".join(lines)


class PlotResult(BaseModel):
    """Result from generating a plot."""
    
    plot_type: str = Field(description="Type of plot")
    title: str = Field(description="Plot title")
    
    # Plot data (one of these will be set)
    image_base64: str | None = Field(
        default=None,
        description="Base64 encoded image",
    )
    image_path: str | None = Field(
        default=None,
        description="Path to saved image",
    )
    plotly_json: dict[str, Any] | None = Field(
        default=None,
        description="Plotly figure as JSON",
    )
    
    # Metadata
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)
