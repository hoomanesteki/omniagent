"""
SQL Agent Module
================
Data querying, filtering, and sampling.
"""

import pandas as pd
import re
from typing import Dict, Any, Optional, List

from agents.base import BaseAgent


class SQLAgent(BaseAgent):
    """Agent for data querying and filtering."""
    
    name = "SQL Agent"
    emoji = "🔍"
    description = "Data querying, filtering, and sampling"
    
    def process(self, query: str) -> Dict[str, Any]:
        """Process SQL-like queries."""
        q = query.lower().strip()
        
        # Extract number from query
        nums = re.findall(r'\d+', query)
        n = min(int(nums[0]), 50) if nums else 10
        
        # Sample queries
        if 'first' in q or 'head' in q:
            return self.sample(n, "first")
        
        if 'last' in q or 'tail' in q:
            return self.sample(n, "last")
        
        if 'random' in q or 'sample' in q:
            return self.sample(n, "random")
        
        # Schema queries
        if 'column' in q or 'schema' in q or 'structure' in q or 'field' in q:
            return self.columns()
        
        # Default: show first rows
        return self.sample(n, "first")
    
    def sample(self, n: int = 10, position: str = "first") -> Dict[str, Any]:
        """Get sample of data."""
        if position == "last":
            data = self.df.tail(n)
            pos_text = "last"
        elif position == "random":
            data = self.df.sample(min(n, len(self.df)))
            pos_text = "random"
        else:
            data = self.df.head(n)
            pos_text = "first"
        
        content = f"""## {self.emoji} {self.name} - Data Preview

### 📋 Showing {pos_text} {len(data)} of {len(self.df):,} rows

*Use the table below to explore the data*"""
        
        insights = f"""**💡 Data Preview:**

• Showing **{len(data)} rows** out of {len(self.df):,} total

• Dataset has **{len(self.df.columns)} columns**

• Try "Show last 10 rows" or "Show random 20 rows" for different views"""
        
        return {
            'content': content,
            'dataframe': data,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def columns(self) -> Dict[str, Any]:
        """Show data schema/columns."""
        summary = self.analyzer.get_summary()
        
        content = f"""## {self.emoji} {self.name} - Data Schema

### 📋 Overview

| Property | Value |
|----------|-------|
| Total Rows | {summary['rows']:,} |
| Total Columns | {summary['columns']} |
| Memory | {summary['memory_mb']:.2f} MB |
| Missing Values | {summary['missing_total']:,} |

---

### 🔢 Numeric Columns ({len(summary['numeric_columns'])})

{', '.join(summary['numeric_columns'][:10]) if summary['numeric_columns'] else 'None'}
{'...' if len(summary['numeric_columns']) > 10 else ''}

---

### 📝 Categorical Columns ({len(summary['categorical_columns'])})

{', '.join(summary['categorical_columns'][:10]) if summary['categorical_columns'] else 'None'}
{'...' if len(summary['categorical_columns']) > 10 else ''}"""
        
        if summary['id_columns']:
            content += f"""

---

### 🔑 ID Columns (auto-excluded from modeling)

{', '.join(summary['id_columns'])}"""
        
        insights = f"""**💡 Schema Summary:**

• **{len(summary['numeric_columns'])} numeric** columns available for analysis

• **{len(summary['categorical_columns'])} categorical** columns available

• {"🔑 " + str(len(summary['id_columns'])) + " ID column(s) detected" if summary['id_columns'] else "No ID columns detected"}

• Use "Describe [column]" for detailed column statistics"""
        
        return {
            'content': content,
            'insights': insights,
            'suggestions': self.get_suggestions()
        }
    
    def get_suggestions(self) -> List[str]:
        """Get suggestions for SQL agent."""
        suggestions = [
            "Show first 10 rows",
            "Show first 20 rows",
            "Show last 10 rows",
            "Show random 15 rows",
            "Show columns",
            "Show statistics",
            "Check missing values",
            "Correlation heatmap"
        ]
        
        return suggestions[:8] + ["🆘 Help", "🏠 Home", "📋 Dataset Info", "ℹ️ About"]
