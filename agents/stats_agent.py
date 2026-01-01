"""
Stats Agent Module
==================
Statistical analysis and data summarization.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List

from agents.base import BaseAgent


class StatsAgent(BaseAgent):
    """Agent for statistical analysis."""
    
    name = "Stats Agent"
    emoji = "📊"
    description = "Statistical analysis, summaries, and missing values"
    
    # Extended patterns for smarter understanding
    STAT_PATTERNS = {
        'mean': ['mean', 'average', 'avg', 'typical', 'central tendency'],
        'median': ['median', 'middle', 'midpoint', '50th', '50%'],
        'std': ['std', 'standard deviation', 'deviation', 'spread', 'variability', 'variance'],
        'min': ['min', 'minimum', 'lowest', 'smallest', 'bottom'],
        'max': ['max', 'maximum', 'highest', 'largest', 'top', 'biggest'],
        'sum': ['sum', 'total', 'aggregate', 'combined'],
        'count': ['count', 'number of', 'how many', 'quantity']
    }
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process statistics-related queries with smart understanding."""
        q = query.lower().strip()
        
        # Smart stat detection
        for stat, patterns in self.STAT_PATTERNS.items():
            if any(p in q for p in patterns):
                col = self._extract_column(q)
                if col and col in self.analyzer.usable_numeric:
                    return self.get_stat(col, stat)
                elif self.analyzer.usable_numeric:
                    # If no column mentioned, try first numeric
                    return self.get_stat(self.analyzer.usable_numeric[0], stat)
        
        # Percentile/quartile requests
        if any(w in q for w in ['%', 'percentile', 'quartile', 'q1', 'q2', 'q3', 'iqr', 'interquartile']):
            col = self._extract_column(q)
            if col:
                return self.describe_column(col)
            elif self.analyzer.usable_numeric:
                return self.describe_column(self.analyzer.usable_numeric[0])
        
        # Missing values analysis
        if any(w in q for w in ['missing', 'null', 'nan', 'empty', 'incomplete', 'na ', 'n/a', 'blank', 'data quality']):
            return self.missing_analysis()
        
        # Distribution/shape analysis
        if any(w in q for w in ['distribution', 'skew', 'normal', 'shape', 'spread']):
            col = self._extract_column(q)
            if col:
                return self.describe_column(col)
        
        # Outlier detection
        if any(w in q for w in ['outlier', 'anomaly', 'unusual', 'extreme']):
            col = self._extract_column(q)
            if col:
                return self.describe_column(col)
            return self.describe_all()
        
        # Summary/overview requests
        if any(w in q for w in ['summary', 'summarize', 'overview', 'describe', 'statistics', 'stats']):
            col = self._extract_column(q)
            if col:
                return self.describe_column(col)
            return self.describe_all()
        
        # Check for specific column mention
        col = self._extract_column(q)
        if col:
            return self.describe_column(col)
        
        # Default: describe all
        return self.describe_all()
    
    def describe_all(self) -> Dict[str, Any]:
        """Get descriptive statistics for all numeric columns."""
        numeric = self.df[self.analyzer.usable_numeric]
        if numeric.empty:
            return self.format_error("No numeric columns found.")
        
        stats = numeric.describe().round(2)
        
        content = f"""## {self.emoji} {self.name} - Statistical Summary

### 📊 Descriptive Statistics for {len(self.analyzer.usable_numeric)} Numeric Columns

| Statistic | {' | '.join(stats.columns[:6])} |
|-----------|{'|'.join([':---:' for _ in stats.columns[:6]])}|"""
        
        for idx in stats.index:
            vals = [f"{stats.loc[idx, c]:,.2f}" if pd.notna(stats.loc[idx, c]) else "N/A" 
                    for c in stats.columns[:6]]
            content += f"\n| {idx} | {' | '.join(vals)} |"
        
        if len(stats.columns) > 6:
            content += f"\n\n*Showing first 6 of {len(stats.columns)} columns*"
        
        # Build detailed insights
        insights_lines = ["**💡 Key Insights & Interpretation:**", ""]
        
        for col in stats.columns[:3]:
            mean = stats.loc['mean', col]
            std = stats.loc['std', col]
            min_val = stats.loc['min', col]
            max_val = stats.loc['max', col]
            cv = std / mean if mean != 0 else 0
            data_range = max_val - min_val
            
            insights_lines.append(f"• **{col}**: Mean = {mean:,.2f}, Std = {std:,.2f}")
            
            # Interpretation of variability
            if cv > 1:
                insights_lines.append(f"  - *High variability detected* (CV={cv:.2f}). This means the values are widely spread around the mean, indicating diverse or inconsistent data.")
            elif cv > 0.5:
                insights_lines.append(f"  - *Moderate variability* (CV={cv:.2f}). The data shows reasonable spread around the central value.")
            else:
                insights_lines.append(f"  - *Low variability* (CV={cv:.2f}). Values are tightly clustered around the mean, indicating consistent data.")
            
            insights_lines.append(f"  - Range: {min_val:,.2f} to {max_val:,.2f} (span of {data_range:,.2f})")
            insights_lines.append("")
        
        # Overall data quality note
        missing = sum(self.analyzer.missing_info[c]['count'] for c in self.analyzer.usable_numeric)
        if missing == 0:
            insights_lines.append("✅ **Data Quality**: All numeric columns have complete data with no missing values.")
        else:
            insights_lines.append(f"⚠️ **Data Quality**: Found {missing:,} missing values across numeric columns. Consider handling these before modeling.")
        
        return {
            'content': content,
            'insights': '\n'.join(insights_lines),
            'suggestions': self.get_suggestions()
        }
    
    def describe_column(self, column: str) -> Dict[str, Any]:
        """Get detailed statistics for a single column."""
        col = self.find_column(column)
        if not col:
            return self.format_error(f"Column '{column}' not found.")
        
        data = self.df[col].dropna()
        
        content = f"""## {self.emoji} {self.name} - Column Analysis: {col}

### 📋 Basic Info

| Property | Value |
|----------|-------|
| Data Type | {self.df[col].dtype} |
| Non-null | {len(data):,} |
| Null | {self.df[col].isnull().sum():,} ({self.df[col].isnull().sum()/len(self.df)*100:.1f}%) |
| Unique | {data.nunique():,} |
| Is ID | {'Yes 🔑' if col in self.analyzer.id_columns else 'No'} |"""
        
        if col in self.analyzer.numeric_cols:
            content += f"""

### 📊 Statistics

| Measure | Value |
|---------|-------|
| Mean | {data.mean():,.4f} |
| Median | {data.median():,.4f} |
| Std Dev | {data.std():,.4f} |
| Min | {data.min():,.4f} |
| Max | {data.max():,.4f} |
| 25% | {data.quantile(0.25):,.4f} |
| 50% | {data.quantile(0.50):,.4f} |
| 75% | {data.quantile(0.75):,.4f} |
| Skewness | {data.skew():,.4f} |"""
            
            Q1, Q3 = data.quantile(0.25), data.quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((data < Q1 - 1.5*IQR) | (data > Q3 + 1.5*IQR)).sum()
            
            insights = f"""**💡 Insights:**

• Range: {data.min():,.2f} to {data.max():,.2f}

• {'Skewed' if abs(data.skew()) > 1 else 'Symmetric'} distribution (skew={data.skew():.2f})

• {outliers} outliers detected ({outliers/len(data)*100:.1f}% of data)"""
        else:
            top = data.value_counts().head(5)
            content += "\n\n### 📝 Top Values\n\n| Value | Count | % |\n|-------|-------|---|"
            for v, c in top.items():
                content += f"\n| {v} | {c:,} | {c/len(data)*100:.1f}% |"
            
            insights = f"""**💡 Insights:**

• {data.nunique()} unique values

• Most common: **'{top.index[0]}'** with {top.iloc[0]:,} occurrences"""
        
        return {
            'content': content,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def get_stat(self, column: str, stat: str) -> Dict[str, Any]:
        """Get a specific statistic for a column."""
        col = self.find_column(column)
        if not col or col not in self.analyzer.numeric_cols:
            return self.format_error(f"Column '{column}' not found or not numeric.")
        
        data = self.df[col].dropna()
        
        stat_map = {
            'mean': data.mean(),
            'average': data.mean(),
            'median': data.median(),
            'std': data.std(),
            'min': data.min(),
            'max': data.max(),
            'sum': data.sum(),
            'count': len(data)
        }
        
        value = stat_map.get(stat.lower())
        
        if value is not None:
            content = f"""## {self.emoji} {self.name} - {stat.title()} of {col}

### 📊 Result

| Statistic | Value |
|-----------|-------|
| {stat.title()} | **{value:,.4f}** |
| Column | {col} |
| Based on | {len(data):,} values |"""
            
            insights = f"""**💡 Context:**

• The {stat} of **{col}** is **{value:,.4f}**

• For reference: min={data.min():,.2f}, max={data.max():,.2f}

• Data range: {data.max() - data.min():,.2f}"""
            
            return {
                'content': content,
                'insights': insights,
                'suggestions': self.get_suggestions()
            }
        
        return self.format_error(f"Could not calculate '{stat}' for {col}")
    
    def missing_analysis(self) -> Dict[str, Any]:
        """Analyze missing values in the dataset."""
        total = sum(m['count'] for m in self.analyzer.missing_info.values())
        
        if total == 0:
            content = f"""## {self.emoji} {self.name} - Missing Values

### ✅ Great News!

Your dataset has **no missing values**! 

All {self.analyzer.row_count:,} rows × {self.analyzer.col_count} columns are complete."""
            
            return {
                'content': content,
                'insights': "**💡 Insight:** Complete data is ideal for analysis and modeling.",
                'suggestions': self.get_suggestions()
            }
        
        total_cells = self.analyzer.row_count * self.analyzer.col_count
        completeness = (1 - total / total_cells) * 100
        
        content = f"""## {self.emoji} {self.name} - Missing Values Analysis

### 📊 Overview

| Metric | Value |
|--------|-------|
| Total cells | {total_cells:,} |
| Missing cells | {total:,} |
| Completeness | {completeness:.1f}% |

### 📋 Columns with Missing Values

| Column | Missing | % | Severity |
|--------|---------|---|----------|"""
        
        cols_missing = [(c, m) for c, m in self.analyzer.missing_info.items() if m['count'] > 0]
        cols_missing.sort(key=lambda x: x[1]['count'], reverse=True)
        
        for col, info in cols_missing[:15]:
            sev = "🔴 High" if info['percent'] > 20 else "🟡 Medium" if info['percent'] > 5 else "🟢 Low"
            content += f"\n| {col} | {info['count']:,} | {info['percent']:.1f}% | {sev} |"
        
        high = [c for c, m in cols_missing if m['percent'] > 20]
        
        insights_lines = ["**💡 Recommendations:**", ""]
        if high:
            insights_lines.append(f"• Consider removing columns with >20% missing: {', '.join(high[:3])}")
            insights_lines.append("")
        insights_lines.append("• Missing values will be auto-handled during modeling")
        insights_lines.append("")
        insights_lines.append(f"• Overall data quality: {completeness:.1f}% complete")
        
        return {
            'content': content,
            'insights': '\n'.join(insights_lines),
            'suggestions': self.get_suggestions()
        }
    
    def _extract_column(self, query: str) -> Optional[str]:
        """Extract column name from query."""
        for col in self.analyzer.all_columns:
            if col.lower() in query.lower():
                return col
        return None
    
    def get_suggestions(self) -> List[str]:
        """Get suggestions for stats agent."""
        suggestions = []
        if self.analyzer.usable_numeric:
            suggestions.extend([
                f"Mean of {self.analyzer.usable_numeric[0]}",
                f"Median of {self.analyzer.usable_numeric[0]}",
                f"Describe {self.analyzer.usable_numeric[0]}",
                "Check missing values"
            ])
        suggestions.extend([
            f"Histogram of {self.analyzer.usable_numeric[0]}" if self.analyzer.usable_numeric else "Show columns",
            "Correlation heatmap",
            "Show all numeric",
            "Show columns"
        ])
        return suggestions[:8] + ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
