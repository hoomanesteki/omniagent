"""
Visualization Agent Module
==========================
Charts, plots, and visual analysis.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, Optional, List

from agents.base import BaseAgent
from core.config import Config


class VizAgent(BaseAgent):
    """Agent for data visualization."""
    
    name = "Visualization Agent"
    emoji = "📈"
    description = "Charts, plots, and visual analysis"
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process visualization-related queries."""
        q = query.lower().strip()
        
        # Extract columns
        cols = [c for c in self.analyzer.all_columns if c.lower() in q]
        num_cols = [c for c in cols if c in self.analyzer.usable_numeric]
        cat_cols = [c for c in cols if c in self.analyzer.usable_categorical]
        
        # Route to specific chart type
        if 'histogram' in q or 'distribution' in q:
            return self.histogram(cols[0] if cols else None)
        
        if 'scatter' in q or 'vs' in q or 'versus' in q:
            return self.scatter(
                num_cols[0] if num_cols else None,
                num_cols[1] if len(num_cols) > 1 else None
            )
        
        if 'bar' in q:
            return self.bar(cols[0] if cols else None)
        
        if 'box' in q or 'outlier' in q:
            return self.box(cols[0] if cols else None)
        
        if 'heatmap' in q or 'correlation' in q or 'corr' in q:
            return self.heatmap()
        
        if 'pie' in q:
            return self.pie(cols[0] if cols else None)
        
        if 'all numeric' in q or 'numeric overview' in q:
            return self.all_numeric()
        
        if 'all categorical' in q or 'categorical overview' in q:
            return self.all_categorical()
        
        # Default: histogram for numeric, bar for categorical
        if num_cols:
            return self.histogram(num_cols[0])
        elif cat_cols:
            return self.bar(cat_cols[0])
        else:
            return self.all_numeric()
    
    def histogram(self, column: str = None) -> Dict[str, Any]:
        """Create histogram for a numeric column."""
        col = self.find_column(column) or (
            self.analyzer.usable_numeric[0] if self.analyzer.usable_numeric else None
        )
        if not col:
            return self.format_error("No numeric column for histogram.")
        
        data = self.df[col].dropna()
        
        fig = px.histogram(
            self.df, x=col, 
            title=f"📊 Distribution of {col}",
            template="plotly_white",
            color_discrete_sequence=[Config.COLORS[0]],
            nbins=30
        )
        fig.add_vline(
            x=data.mean(), 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"Mean: {data.mean():.2f}"
        )
        
        content = f"""## {self.emoji} {self.name} - Histogram: {col}

| Statistic | Value |
|-----------|-------|
| Mean | {data.mean():,.4f} |
| Median | {data.median():,.4f} |
| Std Dev | {data.std():,.4f} |
| Min | {data.min():,.4f} |
| Max | {data.max():,.4f} |"""
        
        skew = data.skew()
        insights = f"""**💡 Distribution Insights:**

• {'Right-skewed (positive skew)' if skew > 1 else 'Left-skewed (negative skew)' if skew < -1 else 'Approximately symmetric'} distribution

• Skewness value: {skew:.2f}

• Data range: {data.max() - data.min():,.2f}

• The red dashed line shows the mean"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def scatter(self, col1: str = None, col2: str = None) -> Dict[str, Any]:
        """Create scatter plot for two numeric columns."""
        cols = self.analyzer.usable_numeric
        x = self.find_column(col1) or (cols[0] if cols else None)
        y = self.find_column(col2) or (cols[1] if len(cols) > 1 else None)
        
        if not x or not y:
            return self.format_error("Need 2 numeric columns for scatter plot.")
        
        fig = px.scatter(
            self.df, x=x, y=y,
            title=f"📈 {x} vs {y}",
            template="plotly_white",
            color_discrete_sequence=[Config.COLORS[0]],
            trendline="ols"
        )
        
        corr = self.df[x].corr(self.df[y])
        strength = "Strong" if abs(corr) >= 0.7 else "Moderate" if abs(corr) >= 0.4 else "Weak"
        direction = "positive" if corr > 0 else "negative"
        
        content = f"""## {self.emoji} {self.name} - Scatter Plot: {x} vs {y}

| Metric | Value |
|--------|-------|
| Correlation | {corr:.4f} |
| Strength | {strength} {direction} |
| R² | {corr**2:.4f} ({corr**2*100:.1f}% variance) |"""
        
        insights = f"""**💡 Relationship Insights:**

• **{strength} {direction}** correlation (r = {corr:.3f})

• {'As ' + x + ' increases, ' + y + ' tends to ' + ('increase' if corr > 0 else 'decrease') if abs(corr) > 0.3 else 'No strong linear pattern detected'}

• The trendline shows the linear relationship

• R² = {corr**2:.3f} means {corr**2*100:.1f}% of variance in {y} is explained by {x}"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def bar(self, column: str = None) -> Dict[str, Any]:
        """Create bar chart for a categorical column."""
        col = self.find_column(column) or (
            self.analyzer.usable_categorical[0] if self.analyzer.usable_categorical else None
        )
        if not col:
            return self.format_error("No column for bar chart.")
        
        counts = self.df[col].value_counts().head(15)
        
        # Horizontal bars for better readability
        fig = px.bar(
            y=counts.index.astype(str), 
            x=counts.values,
            title=f"📊 {col}",
            template="plotly_white",
            color_discrete_sequence=[Config.COLORS[1]],
            orientation='h'
        )
        fig.update_layout(yaxis_title=col, xaxis_title="Count")
        
        total = counts.sum()
        
        content = f"""## {self.emoji} {self.name} - Bar Chart: {col}

| Category | Count | % |
|----------|-------|---|"""
        for cat, cnt in counts.head(10).items():
            content += f"\n| {cat} | {cnt:,} | {cnt/total*100:.1f}% |"
        
        insights = f"""**💡 Category Insights:**

• **{len(counts)} unique categories** in this column

• Most common: **'{counts.index[0]}'** with {counts.iloc[0]:,} occurrences ({counts.iloc[0]/total*100:.1f}%)

• Least common shown: **'{counts.index[-1]}'** with {counts.iloc[-1]:,} occurrences ({counts.iloc[-1]/total*100:.1f}%)

• Horizontal bars used for better readability"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def box(self, column: str = None) -> Dict[str, Any]:
        """Create box plot for a numeric column."""
        col = self.find_column(column) or (
            self.analyzer.usable_numeric[0] if self.analyzer.usable_numeric else None
        )
        if not col:
            return self.format_error("No numeric column for box plot.")
        
        data = self.df[col].dropna()
        
        fig = px.box(
            self.df, y=col,
            title=f"📦 Box Plot: {col}",
            template="plotly_white",
            color_discrete_sequence=[Config.COLORS[0]]
        )
        
        Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((data < Q1 - 1.5*IQR) | (data > Q3 + 1.5*IQR)).sum()
        
        content = f"""## {self.emoji} {self.name} - Box Plot: {col}

| Statistic | Value |
|-----------|-------|
| Q1 (25%) | {Q1:,.4f} |
| Median | {data.median():,.4f} |
| Q3 (75%) | {Q3:,.4f} |
| IQR | {IQR:,.4f} |
| Outliers | {outliers} ({outliers/len(data)*100:.1f}%) |"""
        
        insights = f"""**💡 Box Plot Insights:**

• {'⚠️ **' + str(outliers) + ' outliers detected** - values outside Q1-1.5×IQR to Q3+1.5×IQR' if outliers > 0 else '✅ **No significant outliers** detected'}

• Interquartile Range (IQR): {IQR:,.2f}

• 50% of data falls between {Q1:,.2f} and {Q3:,.2f}

• Consider investigating outliers before modeling"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def heatmap(self) -> Dict[str, Any]:
        """Create correlation heatmap."""
        cols = self.analyzer.usable_numeric
        if len(cols) < 2:
            return self.format_error("Need 2+ numeric columns for heatmap.")
        
        corr = self.df[cols[:12]].corr()
        
        fig = px.imshow(
            corr,
            title="🔥 Correlation Heatmap",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            template="plotly_white",
            text_auto=".2f"
        )
        fig.update_layout(height=650)
        
        # Find strong correlations
        strong = []
        for i in range(len(corr.columns)):
            for j in range(i+1, len(corr.columns)):
                v = corr.iloc[i, j]
                if abs(v) > 0.6:
                    strong.append(f"  - {corr.columns[i]} ↔ {corr.columns[j]}: {v:.2f}")
        
        content = f"""## {self.emoji} {self.name} - Correlation Heatmap

Showing correlations between {len(cols[:12])} numeric columns.

**Color Scale:** Red = Positive, Blue = Negative"""
        
        if strong:
            insights = "**💡 Strong Correlations Found (|r| > 0.6):**\n\n" + "\n\n".join(strong[:5])
        else:
            insights = "**💡 Insight:** No very strong correlations (|r| > 0.6) found between numeric columns."
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def pie(self, column: str = None) -> Dict[str, Any]:
        """Create pie chart for a categorical column."""
        col = self.find_column(column) or (
            self.analyzer.usable_categorical[0] if self.analyzer.usable_categorical else None
        )
        if not col:
            return self.format_error("No column for pie chart.")
        
        counts = self.df[col].value_counts().head(10)
        
        fig = px.pie(
            values=counts.values,
            names=counts.index,
            title=f"🥧 {col}",
            template="plotly_white",
            color_discrete_sequence=Config.COLORS
        )
        
        content = f"""## {self.emoji} {self.name} - Pie Chart: {col}

Showing distribution of top {len(counts)} categories."""
        
        insights = f"""**💡 Pie Chart Insights:**

• **'{counts.index[0]}'** is the largest segment ({counts.iloc[0]/counts.sum()*100:.1f}%)

• Top 3 categories account for {counts.head(3).sum()/counts.sum()*100:.1f}% of data

• Useful for seeing proportions at a glance"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def all_numeric(self) -> Dict[str, Any]:
        """Show all numeric column distributions."""
        cols = self.analyzer.usable_numeric[:12]
        if not cols:
            return self.format_error("No numeric columns.")
        
        n_rows = (len(cols) + 2) // 3
        fig = make_subplots(rows=n_rows, cols=3, subplot_titles=cols)
        
        for i, col in enumerate(cols):
            fig.add_trace(
                go.Histogram(x=self.df[col], name=col, marker_color=Config.COLORS[i % len(Config.COLORS)]),
                row=i//3+1, col=i%3+1
            )
        
        fig.update_layout(
            title="📊 All Numeric Distributions",
            height=300*n_rows,
            showlegend=False,
            template="plotly_white"
        )
        
        content = f"## {self.emoji} {self.name} - All {len(cols)} Numeric Columns"
        
        insights = f"""**📊 Numeric Overview:**

• Showing distributions for **{len(cols)} numeric columns**

• Use histograms to identify skewness, outliers, and patterns

• Try "Box plot of [column]" for detailed outlier detection

• Try "Histogram of [column]" for a larger view"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def all_categorical(self) -> Dict[str, Any]:
        """Show all categorical column distributions."""
        cols = self.analyzer.usable_categorical[:9]
        if not cols:
            return self.format_error("No categorical columns.")
        
        n_rows = (len(cols) + 2) // 3
        fig = make_subplots(rows=n_rows, cols=3, subplot_titles=cols)
        
        for i, col in enumerate(cols):
            counts = self.df[col].value_counts().head(8)
            # Horizontal bars for better readability
            fig.add_trace(
                go.Bar(
                    y=counts.index.astype(str),
                    x=counts.values,
                    orientation='h',
                    marker_color=Config.COLORS[i % len(Config.COLORS)]
                ),
                row=i//3+1, col=i%3+1
            )
        
        fig.update_layout(
            title="📊 All Categorical Distributions",
            height=400*n_rows,
            showlegend=False,
            template="plotly_white"
        )
        
        content = f"## {self.emoji} {self.name} - All {len(cols)} Categorical Columns"
        
        # Generate insights
        cat_insights = []
        for col in cols[:3]:
            counts = self.df[col].value_counts()
            cat_insights.append(f"  - **{col}**: {counts.nunique()} categories, top: '{counts.index[0]}' ({counts.iloc[0]/len(self.df)*100:.1f}%)")
        
        insights = f"""**📝 Categorical Overview:**

{chr(10).join(cat_insights)}

• Horizontal bars show category counts for better readability

• Look for class imbalance before modeling"""
        
        return {
            'content': content,
            'figure': fig,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def get_suggestions(self) -> List[str]:
        """Get suggestions for viz agent."""
        num = self.analyzer.usable_numeric
        cat = self.analyzer.usable_categorical
        
        suggestions = [
            f"Histogram of {num[0]}" if num else "Show statistics",
            f"Box plot of {num[0]}" if num else "Check missing",
            f"Scatter {num[0]} vs {num[1]}" if len(num) > 1 else "Correlation heatmap",
            f"Bar chart of {cat[0]}" if cat else "Show columns",
            "Correlation heatmap",
            "Show all numeric",
            "Show all categorical",
            f"Pie chart of {cat[0]}" if cat else "Show statistics"
        ]
        
        return suggestions[:8] + ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
