"""
Plot Agent - Visualization tools.

Provides tools for:
- Histograms
- Scatter plots
- Box plots
- Correlation heatmaps
- Bar charts
"""

import base64
import io
from typing import Any

from omniagent.agents.base import BaseAgent
from omniagent.mcp.server import mcp_tool


class PlotAgent(BaseAgent):
    """
    Agent for generating visualizations.
    
    Tools:
    - histogram: Distribution plot
    - scatter: Scatter plot
    - boxplot: Box plot
    - heatmap: Correlation heatmap
    - bar: Bar chart
    """
    
    name = "plot_agent"
    description = "Generates data visualizations"
    
    def _fig_to_base64(self, fig: Any) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    
    def _ensure_matplotlib(self) -> tuple[Any, Any]:
        """Import and configure matplotlib."""
        try:
            import matplotlib
            matplotlib.use("Agg")  # Non-interactive backend
            import matplotlib.pyplot as plt
            return matplotlib, plt
        except ImportError:
            raise ImportError("matplotlib not installed. Run: pip install matplotlib")
    
    @mcp_tool
    def histogram(
        self,
        column: str,
        bins: int = 30,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a histogram for a numeric column.
        
        Args:
            column: Column to plot
            bins: Number of bins (default 30)
            title: Plot title (optional)
            
        Returns:
            Dictionary with base64 encoded image
        """
        try:
            _, plt = self._ensure_matplotlib()
            import numpy as np
        except ImportError as e:
            return {"error": str(e)}
        
        table_name = self._get_table_name()
        
        # Validate column
        valid, error = self._validate_columns(table_name, [column])
        if not valid:
            return {"error": error}
        
        # Fetch data
        result = self.db.connection.execute(f"""
            SELECT "{column}"
            FROM {table_name}
            WHERE "{column}" IS NOT NULL
        """)
        data = [row[0] for row in result.fetchall()]
        
        if not data:
            return {"error": f"No data in column '{column}'"}
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(data, bins=bins, edgecolor="black", alpha=0.7)
        ax.set_xlabel(column)
        ax.set_ylabel("Frequency")
        ax.set_title(title or f"Distribution of {column}")
        ax.grid(True, alpha=0.3)
        
        # Convert to base64
        image_b64 = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            "plot_type": "histogram",
            "column": column,
            "data_points": len(data),
            "bins": bins,
            "image_base64": image_b64,
        }
    
    @mcp_tool
    def scatter(
        self,
        x_column: str,
        y_column: str,
        color_column: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a scatter plot.
        
        Args:
            x_column: Column for x-axis
            y_column: Column for y-axis
            color_column: Column for color coding (optional)
            title: Plot title (optional)
            
        Returns:
            Dictionary with base64 encoded image
        """
        try:
            _, plt = self._ensure_matplotlib()
            import numpy as np
        except ImportError as e:
            return {"error": str(e)}
        
        table_name = self._get_table_name()
        
        # Validate columns
        columns = [x_column, y_column]
        if color_column:
            columns.append(color_column)
        
        valid, error = self._validate_columns(table_name, columns)
        if not valid:
            return {"error": error}
        
        # Fetch data
        columns_sql = ", ".join(f'"{c}"' for c in columns)
        where_clause = " AND ".join(f'"{c}" IS NOT NULL' for c in [x_column, y_column])
        
        result = self.db.connection.execute(f"""
            SELECT {columns_sql}
            FROM {table_name}
            WHERE {where_clause}
            LIMIT 5000
        """)
        data = result.fetchall()
        
        if not data:
            return {"error": "No data to plot"}
        
        x_data = [row[0] for row in data]
        y_data = [row[1] for row in data]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if color_column:
            color_data = [row[2] for row in data]
            scatter = ax.scatter(x_data, y_data, c=range(len(color_data)), 
                                cmap="viridis", alpha=0.6)
            plt.colorbar(scatter, label=color_column)
        else:
            ax.scatter(x_data, y_data, alpha=0.6)
        
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        ax.set_title(title or f"{y_column} vs {x_column}")
        ax.grid(True, alpha=0.3)
        
        # Convert to base64
        image_b64 = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            "plot_type": "scatter",
            "x_column": x_column,
            "y_column": y_column,
            "data_points": len(data),
            "image_base64": image_b64,
        }
    
    @mcp_tool
    def boxplot(
        self,
        column: str,
        group_by: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a box plot.
        
        Args:
            column: Numeric column to plot
            group_by: Categorical column to group by (optional)
            title: Plot title (optional)
            
        Returns:
            Dictionary with base64 encoded image
        """
        try:
            _, plt = self._ensure_matplotlib()
        except ImportError as e:
            return {"error": str(e)}
        
        table_name = self._get_table_name()
        
        # Validate columns
        columns = [column]
        if group_by:
            columns.append(group_by)
        
        valid, error = self._validate_columns(table_name, columns)
        if not valid:
            return {"error": error}
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if group_by:
            # Get unique groups
            result = self.db.connection.execute(f"""
                SELECT DISTINCT "{group_by}"
                FROM {table_name}
                WHERE "{group_by}" IS NOT NULL
                ORDER BY "{group_by}"
                LIMIT 20
            """)
            groups = [row[0] for row in result.fetchall()]
            
            # Get data for each group
            data_by_group = []
            for group in groups:
                result = self.db.connection.execute(f"""
                    SELECT "{column}"
                    FROM {table_name}
                    WHERE "{column}" IS NOT NULL AND "{group_by}" = ?
                """, [group])
                data_by_group.append([row[0] for row in result.fetchall()])
            
            ax.boxplot(data_by_group, labels=[str(g) for g in groups])
            ax.set_xlabel(group_by)
        else:
            result = self.db.connection.execute(f"""
                SELECT "{column}"
                FROM {table_name}
                WHERE "{column}" IS NOT NULL
            """)
            data = [row[0] for row in result.fetchall()]
            ax.boxplot(data)
        
        ax.set_ylabel(column)
        ax.set_title(title or f"Box Plot of {column}")
        ax.grid(True, alpha=0.3)
        
        # Rotate x labels if grouped
        if group_by:
            plt.xticks(rotation=45, ha="right")
        
        # Convert to base64
        image_b64 = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            "plot_type": "boxplot",
            "column": column,
            "group_by": group_by,
            "image_base64": image_b64,
        }
    
    @mcp_tool
    def heatmap(
        self,
        columns: list[str] | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a correlation heatmap.
        
        Args:
            columns: Columns to include. None for all numeric columns.
            title: Plot title (optional)
            
        Returns:
            Dictionary with base64 encoded image
        """
        try:
            _, plt = self._ensure_matplotlib()
            import numpy as np
        except ImportError as e:
            return {"error": str(e)}
        
        table_name = self._get_table_name()
        
        # Get numeric columns
        if columns is None:
            columns = self._get_numeric_columns(table_name)
        else:
            valid, error = self._validate_columns(table_name, columns)
            if not valid:
                return {"error": error}
            numeric = self._get_numeric_columns(table_name)
            columns = [c for c in columns if c in numeric]
        
        if len(columns) < 2:
            return {"error": "Need at least 2 numeric columns for heatmap"}
        
        # Compute correlation matrix
        n = len(columns)
        corr_matrix = np.zeros((n, n))
        
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    result = self.db.connection.execute(f"""
                        SELECT CORR("{col1}", "{col2}")
                        FROM {table_name}
                        WHERE "{col1}" IS NOT NULL AND "{col2}" IS NOT NULL
                    """)
                    corr = result.fetchone()[0]
                    corr_matrix[i, j] = corr if corr is not None else 0
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr_matrix, cmap="RdBu_r", vmin=-1, vmax=1)
        
        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.set_label("Correlation")
        
        # Add labels
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(columns, rotation=45, ha="right")
        ax.set_yticklabels(columns)
        
        # Add values
        for i in range(n):
            for j in range(n):
                value = corr_matrix[i, j]
                color = "white" if abs(value) > 0.5 else "black"
                ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=color, fontsize=8)
        
        ax.set_title(title or "Correlation Heatmap")
        plt.tight_layout()
        
        # Convert to base64
        image_b64 = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            "plot_type": "heatmap",
            "columns": columns,
            "image_base64": image_b64,
        }
    
    @mcp_tool
    def bar(
        self,
        x_column: str,
        y_column: str | None = None,
        aggregation: str = "count",
        top_n: int = 20,
        title: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a bar chart.
        
        Args:
            x_column: Column for x-axis (categories)
            y_column: Column to aggregate (optional, used with aggregation)
            aggregation: How to aggregate - 'count', 'sum', 'avg', 'min', 'max'
            top_n: Number of bars to show (default 20)
            title: Plot title (optional)
            
        Returns:
            Dictionary with base64 encoded image
        """
        try:
            _, plt = self._ensure_matplotlib()
        except ImportError as e:
            return {"error": str(e)}
        
        table_name = self._get_table_name()
        
        # Validate columns
        columns = [x_column]
        if y_column:
            columns.append(y_column)
        
        valid, error = self._validate_columns(table_name, columns)
        if not valid:
            return {"error": error}
        
        top_n = min(max(1, top_n), 50)
        
        # Build query
        if y_column and aggregation != "count":
            agg_map = {"sum": "SUM", "avg": "AVG", "min": "MIN", "max": "MAX"}
            agg_func = agg_map.get(aggregation, "AVG")
            result = self.db.connection.execute(f"""
                SELECT "{x_column}", {agg_func}("{y_column}") as value
                FROM {table_name}
                WHERE "{x_column}" IS NOT NULL
                GROUP BY "{x_column}"
                ORDER BY value DESC
                LIMIT {top_n}
            """)
            y_label = f"{aggregation}({y_column})"
        else:
            result = self.db.connection.execute(f"""
                SELECT "{x_column}", COUNT(*) as value
                FROM {table_name}
                WHERE "{x_column}" IS NOT NULL
                GROUP BY "{x_column}"
                ORDER BY value DESC
                LIMIT {top_n}
            """)
            y_label = "Count"
        
        data = result.fetchall()
        
        if not data:
            return {"error": "No data to plot"}
        
        x_data = [str(row[0]) for row in data]
        y_data = [row[1] for row in data]
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(range(len(x_data)), y_data, color="steelblue", edgecolor="black")
        
        ax.set_xticks(range(len(x_data)))
        ax.set_xticklabels(x_data, rotation=45, ha="right")
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_label)
        ax.set_title(title or f"{y_label} by {x_column}")
        ax.grid(True, alpha=0.3, axis="y")
        
        plt.tight_layout()
        
        # Convert to base64
        image_b64 = self._fig_to_base64(fig)
        plt.close(fig)
        
        return {
            "plot_type": "bar",
            "x_column": x_column,
            "aggregation": aggregation,
            "bars": len(data),
            "image_base64": image_b64,
        }
