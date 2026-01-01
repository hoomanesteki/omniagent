"""
Data Analyzer Module
====================
Comprehensive data analysis and feature detection.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any


class DataAnalyzer:
    """Analyzes DataFrame and extracts metadata."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._analyze()
    
    def _analyze(self):
        """Run all analysis on the dataframe."""
        self.all_columns = self.df.columns.tolist()
        self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        self.categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Detect ID columns
        self.id_columns = self._detect_ids()
        
        # Usable columns (excluding IDs)
        self.usable_numeric = [c for c in self.numeric_cols if c not in self.id_columns]
        self.usable_categorical = [c for c in self.categorical_cols if c not in self.id_columns]
        
        # Missing value info
        self.missing_info = self._analyze_missing()
        
        # Basic stats
        self.row_count = len(self.df)
        self.col_count = len(self.df.columns)
        self.memory_usage = self.df.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Target candidates
        self.target_candidates = self._detect_targets()
    
    def _detect_ids(self) -> List[str]:
        """Detect ID columns using multiple heuristics."""
        ids = []
        id_patterns = ['_id', 'id_', 'index', 'key', 'uuid', '_key', '_idx']
        exact_ids = ['id', 'index', 'row', 'unnamed: 0']
        
        for col in self.df.columns:
            col_lower = col.lower().strip()
            
            # Check exact matches
            if col_lower in exact_ids:
                ids.append(col)
                continue
            
            # Check patterns
            if any(p in col_lower for p in id_patterns):
                ids.append(col)
                continue
            
            # Check numeric monotonic unique
            if col in self.numeric_cols:
                series = self.df[col].dropna()
                if len(series) > 10:
                    if series.is_monotonic_increasing and series.nunique() == len(series):
                        ids.append(col)
        
        return ids
    
    def _analyze_missing(self) -> Dict[str, Dict]:
        """Analyze missing values for all columns."""
        result = {}
        for col in self.df.columns:
            count = int(self.df[col].isnull().sum())
            percent = round(count / len(self.df) * 100, 2) if len(self.df) > 0 else 0
            result[col] = {'count': count, 'percent': percent}
        return result
    
    def _detect_targets(self) -> List[Dict]:
        """Detect potential prediction target columns."""
        candidates = []
        
        for col in self.df.columns:
            if col in self.id_columns:
                continue
            
            data = self.df[col].dropna()
            if len(data) == 0:
                continue
            
            if col in self.categorical_cols:
                n_unique = data.nunique()
                if 2 <= n_unique <= 20:
                    candidates.append({
                        'column': col,
                        'type': 'classification',
                        'classes': n_unique
                    })
            elif col in self.numeric_cols:
                n_unique = data.nunique()
                if n_unique <= 10:
                    candidates.append({
                        'column': col,
                        'type': 'classification',
                        'classes': n_unique
                    })
                else:
                    candidates.append({
                        'column': col,
                        'type': 'regression',
                        'classes': None
                    })
        
        return candidates[:8]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive data summary."""
        return {
            'rows': self.row_count,
            'columns': self.col_count,
            'memory_mb': round(self.memory_usage, 2),
            'numeric_columns': self.usable_numeric,
            'categorical_columns': self.usable_categorical,
            'id_columns': self.id_columns,
            'all_columns': self.all_columns,
            'missing_total': sum(m['count'] for m in self.missing_info.values())
        }
    
    def detect_problem_type(self, target: str) -> str:
        """Detect if target is classification or regression."""
        if target not in self.df.columns:
            return "unknown"
        
        if target in self.categorical_cols:
            return "classification"
        
        if target in self.numeric_cols:
            n_unique = self.df[target].dropna().nunique()
            return "classification" if n_unique <= 10 else "regression"
        
        return "unknown"
    
    def get_column_stats(self, column: str) -> Optional[Dict]:
        """Get detailed statistics for a column."""
        if column not in self.df.columns:
            return None
        
        data = self.df[column].dropna()
        
        if column in self.numeric_cols:
            return {
                'type': 'numeric',
                'count': len(data),
                'mean': data.mean(),
                'median': data.median(),
                'std': data.std(),
                'min': data.min(),
                'max': data.max(),
                'q25': data.quantile(0.25),
                'q75': data.quantile(0.75),
                'skew': data.skew(),
                'missing': self.missing_info[column]
            }
        else:
            counts = data.value_counts()
            return {
                'type': 'categorical',
                'count': len(data),
                'unique': data.nunique(),
                'top': counts.index[0] if len(counts) > 0 else None,
                'top_count': counts.iloc[0] if len(counts) > 0 else 0,
                'missing': self.missing_info[column]
            }
    
    def find_column(self, name: str) -> Optional[str]:
        """Find column by name (case-insensitive, partial match)."""
        if not name:
            return None
        
        name_lower = name.lower().strip()
        
        # Exact match
        for col in self.all_columns:
            if col.lower() == name_lower:
                return col
        
        # Partial match
        for col in self.all_columns:
            if name_lower in col.lower():
                return col
        
        return None
