"""
Aggregate Agent Module
======================
Data aggregation, groupby operations, and summary computations.
Smart agent that guides users through aggregation operations.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, Optional, List

from agents.base import BaseAgent
from core.config import Config


class AggregateAgent(BaseAgent):
    """Agent for data aggregation and groupby operations."""
    
    name = "Aggregate Agent"
    emoji = "📦"
    description = "Data aggregation, groupby, pivot tables, and summary computations"
    
    # Patterns for smart understanding
    AGG_PATTERNS = {
        'groupby': ['group by', 'groupby', 'grouped by', 'by group', 'per group', 
                    'for each', 'by each', 'breakdown by', 'split by'],
        'aggregate': ['aggregate', 'aggregation', 'agg', 'summarize by', 'summary by'],
        'pivot': ['pivot', 'pivot table', 'cross tab', 'crosstab', 'cross tabulation'],
        'count_by': ['count by', 'count per', 'how many per', 'number of per', 'counts per'],
        'sum_by': ['sum by', 'total by', 'sum per', 'total per', 'totals by'],
        'avg_by': ['average by', 'mean by', 'avg per', 'average per', 'mean per'],
        'max_by': ['max by', 'maximum by', 'highest by', 'max per', 'largest per'],
        'min_by': ['min by', 'minimum by', 'lowest by', 'min per', 'smallest per'],
    }
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process aggregation-related queries with smart understanding."""
        q = query.lower().strip()
        
        # Detect aggregation type
        agg_type = self._detect_agg_type(q)
        
        # Extract columns mentioned
        group_col = self._find_categorical_column(q)
        value_col = self._find_numeric_column(q)
        
        # Handle different scenarios
        if agg_type == 'pivot':
            return self._pivot_guide()
        
        if agg_type == 'groupby' or agg_type == 'aggregate':
            if group_col and value_col:
                return self.groupby_agg(group_col, value_col, 'mean')
            elif group_col:
                return self.groupby_summary(group_col)
            else:
                return self._interactive_aggregator()
        
        if agg_type == 'count_by':
            if group_col:
                return self.count_by(group_col)
            return self._interactive_aggregator()
        
        if agg_type == 'sum_by':
            if group_col and value_col:
                return self.groupby_agg(group_col, value_col, 'sum')
            return self._interactive_aggregator()
        
        if agg_type == 'avg_by':
            if group_col and value_col:
                return self.groupby_agg(group_col, value_col, 'mean')
            return self._interactive_aggregator()
        
        if agg_type == 'max_by':
            if group_col and value_col:
                return self.groupby_agg(group_col, value_col, 'max')
            return self._interactive_aggregator()
        
        if agg_type == 'min_by':
            if group_col and value_col:
                return self.groupby_agg(group_col, value_col, 'min')
            return self._interactive_aggregator()
        
        # Default: interactive guide
        return self._interactive_aggregator()
    
    def _detect_agg_type(self, query: str) -> Optional[str]:
        """Detect aggregation type from query."""
        for agg_type, patterns in self.AGG_PATTERNS.items():
            if any(p in query for p in patterns):
                return agg_type
        return None
    
    def _find_categorical_column(self, query: str) -> Optional[str]:
        """Find categorical column in query."""
        for col in self.analyzer.usable_categorical:
            if col.lower() in query.lower():
                return col
        return None
    
    def _find_numeric_column(self, query: str) -> Optional[str]:
        """Find numeric column in query."""
        for col in self.analyzer.usable_numeric:
            if col.lower() in query.lower():
                return col
        return None
    
    def _interactive_aggregator(self) -> Dict[str, Any]:
        """Interactive guide for aggregation operations."""
        cat_cols = self.analyzer.usable_categorical
        num_cols = self.analyzer.usable_numeric
        
        content = f"""## {self.emoji} {self.name} - Aggregation Builder

### 🛠️ Let's Create an Aggregation!

I can help you summarize data by groups. Here's what's available:

---

### 📝 Group By Columns (Categorical)

These columns can be used to create groups:

| # | Column | Unique Values | Example |
|---|--------|---------------|---------|"""
        
        for i, col in enumerate(cat_cols[:6], 1):
            unique = self.df[col].nunique()
            example = str(self.df[col].dropna().iloc[0])[:20] if len(self.df[col].dropna()) > 0 else 'N/A'
            content += f"\n| {i} | **{col}** | {unique} | {example} |"
        
        content += f"""

---

### 🔢 Value Columns (Numeric)

These columns can be aggregated (sum, mean, etc.):

| # | Column | Type |
|---|--------|------|"""
        
        for i, col in enumerate(num_cols[:6], 1):
            content += f"\n| {i} | **{col}** | Numeric |"
        
        content += f"""

---

### 💡 Example Commands

**Count by category:**
- "Count by {cat_cols[0]}" if cat_cols else "Count by category"

**Sum/Average by group:**
- "Sum {num_cols[0]} by {cat_cols[0]}" if num_cols and cat_cols else "Sum values by category"
- "Average {num_cols[0]} by {cat_cols[0]}" if num_cols and cat_cols else "Average by category"

**Group summary:**
- "Group by {cat_cols[0]}" if cat_cols else "Group by category"

---

### 🎯 Available Operations

| Operation | Description | Example |
|-----------|-------------|---------|
| **count** | Count rows per group | "Count by gender" |
| **sum** | Sum values per group | "Sum sales by region" |
| **mean/avg** | Average per group | "Average price by category" |
| **max** | Maximum per group | "Max revenue by month" |
| **min** | Minimum per group | "Min cost by department" |
"""
        
        insights = f"""**💡 Aggregation Guide:**

• **{len(cat_cols)} categorical columns** available for grouping

• **{len(num_cols)} numeric columns** available for aggregation

• Click a suggestion below or type your aggregation request!

• Example: "Average {num_cols[0] if num_cols else 'value'} by {cat_cols[0] if cat_cols else 'category'}" """
        
        return {
            'content': content,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def count_by(self, group_col: str) -> Dict[str, Any]:
        """Count rows by group."""
        col = self.find_column(group_col)
        if not col:
            return self.format_error(f"Column '{group_col}' not found.")
        
        # Perform aggregation
        counts = self.df[col].value_counts().reset_index()
        counts.columns = [col, 'Count']
        
        # Create chart
        fig = px.bar(
            counts.head(15),
            y=col,
            x='Count',
            orientation='h',
            title=f"📊 Count by {col}",
            template="plotly_white",
            color='Count',
            color_continuous_scale='Blues'
        )
        fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
        
        content = f"""## {self.emoji} {self.name} - Count by {col}

### 📊 Row Counts per Group

| {col} | Count | Percentage |
|-------|-------|------------|"""
        
        total = counts['Count'].sum()
        for _, row in counts.head(10).iterrows():
            pct = row['Count'] / total * 100
            content += f"\n| {row[col]} | {row['Count']:,} | {pct:.1f}% |"
        
        if len(counts) > 10:
            content += f"\n\n*Showing top 10 of {len(counts)} groups*"
        
        # Insights
        top_group = counts.iloc[0][col]
        top_count = counts.iloc[0]['Count']
        top_pct = top_count / total * 100
        
        insights = f"""**💡 Count Analysis:**

• **{len(counts)} unique groups** found in '{col}'

• **Top group:** '{top_group}' with {top_count:,} rows ({top_pct:.1f}%)

• **Total rows:** {total:,}

• Distribution shows {"balanced groups" if counts['Count'].std() / counts['Count'].mean() < 0.5 else "imbalanced groups - some categories dominate"}"""
        
        return {
            'content': content,
            'figure': fig,
            'dataframe': counts.head(15),
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def groupby_agg(self, group_col: str, value_col: str, agg_func: str = 'mean') -> Dict[str, Any]:
        """Aggregate a value column by a group column."""
        g_col = self.find_column(group_col)
        v_col = self.find_column(value_col)
        
        if not g_col:
            return self.format_error(f"Group column '{group_col}' not found.")
        if not v_col:
            return self.format_error(f"Value column '{value_col}' not found.")
        
        # Map function names
        func_map = {
            'mean': 'mean', 'avg': 'mean', 'average': 'mean',
            'sum': 'sum', 'total': 'sum',
            'max': 'max', 'maximum': 'max',
            'min': 'min', 'minimum': 'min',
            'count': 'count', 'std': 'std'
        }
        func = func_map.get(agg_func.lower(), 'mean')
        func_label = {'mean': 'Average', 'sum': 'Total', 'max': 'Maximum', 'min': 'Minimum', 'count': 'Count', 'std': 'Std Dev'}
        
        # Perform aggregation
        result = self.df.groupby(g_col)[v_col].agg(func).reset_index()
        result.columns = [g_col, f'{func_label.get(func, func)} of {v_col}']
        result = result.sort_values(result.columns[1], ascending=False)
        
        # Create chart
        fig = px.bar(
            result.head(15),
            y=g_col,
            x=result.columns[1],
            orientation='h',
            title=f"📊 {func_label.get(func, func)} of {v_col} by {g_col}",
            template="plotly_white",
            color=result.columns[1],
            color_continuous_scale='Viridis'
        )
        fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
        
        content = f"""## {self.emoji} {self.name} - {func_label.get(func, func)} by Group

### 📊 {func_label.get(func, func)} of {v_col} by {g_col}

| {g_col} | {func_label.get(func, func)} of {v_col} |
|---------|-------|"""
        
        for _, row in result.head(10).iterrows():
            val = row[result.columns[1]]
            content += f"\n| {row[g_col]} | {val:,.2f} |"
        
        if len(result) > 10:
            content += f"\n\n*Showing top 10 of {len(result)} groups*"
        
        # Calculate insights
        top_group = result.iloc[0][g_col]
        top_val = result.iloc[0][result.columns[1]]
        bottom_group = result.iloc[-1][g_col]
        bottom_val = result.iloc[-1][result.columns[1]]
        overall = self.df[v_col].agg(func)
        
        insights = f"""**💡 Aggregation Insights:**

• **Highest:** '{top_group}' with {func_label.get(func, func).lower()} of {top_val:,.2f}

• **Lowest:** '{bottom_group}' with {func_label.get(func, func).lower()} of {bottom_val:,.2f}

• **Overall {func_label.get(func, func).lower()}:** {overall:,.2f}

• **Difference:** Top is {(top_val/bottom_val - 1)*100:.1f}% higher than bottom

• **Groups analyzed:** {len(result)}"""
        
        return {
            'content': content,
            'figure': fig,
            'dataframe': result.head(15),
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def groupby_summary(self, group_col: str) -> Dict[str, Any]:
        """Get comprehensive summary for each group."""
        col = self.find_column(group_col)
        if not col:
            return self.format_error(f"Column '{group_col}' not found.")
        
        # Get numeric columns for aggregation
        num_cols = self.analyzer.usable_numeric[:5]
        
        if not num_cols:
            return self.count_by(col)
        
        # Perform multiple aggregations
        aggs = {c: ['mean', 'sum', 'count'] for c in num_cols[:3]}
        result = self.df.groupby(col).agg(aggs).round(2)
        result.columns = ['_'.join(c) for c in result.columns]
        result = result.reset_index()
        
        content = f"""## {self.emoji} {self.name} - Group Summary

### 📊 Summary by {col}

**Groups:** {self.df[col].nunique()} unique values

---

### 📈 Aggregated Statistics

"""
        
        # Show simplified table
        simple_result = self.df.groupby(col)[num_cols[0]].agg(['mean', 'sum', 'count']).round(2)
        simple_result = simple_result.reset_index()
        simple_result.columns = [col, 'Mean', 'Sum', 'Count']
        
        content += f"| {col} | Mean ({num_cols[0]}) | Sum | Count |\n"
        content += f"|-------|------|-----|-------|\n"
        
        for _, row in simple_result.head(10).iterrows():
            content += f"| {row[col]} | {row['Mean']:,.2f} | {row['Sum']:,.2f} | {int(row['Count']):,} |\n"
        
        # Create chart
        fig = px.bar(
            simple_result.head(10),
            x=col,
            y='Mean',
            title=f"📊 Mean of {num_cols[0]} by {col}",
            template="plotly_white",
            color='Mean',
            color_continuous_scale='Blues'
        )
        
        insights = f"""**💡 Group Summary:**

• **{self.df[col].nunique()} groups** analyzed

• Showing mean, sum, and count for '{num_cols[0]}'

• Try "Sum {num_cols[0]} by {col}" for specific aggregations

• Try "Count by {col}" for row counts only"""
        
        return {
            'content': content,
            'figure': fig,
            'dataframe': simple_result,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def _pivot_guide(self) -> Dict[str, Any]:
        """Guide for pivot table creation."""
        cat_cols = self.analyzer.usable_categorical
        num_cols = self.analyzer.usable_numeric
        
        content = f"""## {self.emoji} {self.name} - Pivot Table Guide

### 📊 Creating Pivot Tables

Pivot tables let you summarize data by two categorical dimensions.

---

### 🎯 Available Columns

**For Rows/Columns (Categorical):**
{', '.join(cat_cols[:5]) if cat_cols else 'No categorical columns'}

**For Values (Numeric):**
{', '.join(num_cols[:5]) if num_cols else 'No numeric columns'}

---

### 💡 How to Create

Currently, I can help with simpler aggregations. Try:

- "Group by {cat_cols[0]}" if cat_cols else "Group by category"
- "Average {num_cols[0]} by {cat_cols[0]}" if num_cols and cat_cols else "Average by category"
- "Count by {cat_cols[0]}" if cat_cols else "Count by category"
"""
        
        return {
            'content': content,
            'insights': "**💡 Tip:** For complex pivot tables, try simple group-by operations first!",
            'suggestions': self.get_suggestions()
        }
    
    def get_suggestions(self) -> List[str]:
        """Get suggestions for aggregate agent."""
        cat = self.analyzer.usable_categorical
        num = self.analyzer.usable_numeric
        
        suggestions = []
        
        if cat:
            suggestions.append(f"Count by {cat[0]}")
            suggestions.append(f"Group by {cat[0]}")
        if cat and num:
            suggestions.append(f"Sum {num[0]} by {cat[0]}")
            suggestions.append(f"Average {num[0]} by {cat[0]}")
            suggestions.append(f"Max {num[0]} by {cat[0]}")
        
        suggestions.extend([
            "Show statistics",
            "Correlation heatmap",
            "Show all categorical"
        ])
        
        return suggestions[:8] + ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
