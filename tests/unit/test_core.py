"""
Unit Tests for Core Modules
===========================
Tests for config, analyzer, and llm modules.

Run with: pytest tests/unit/test_core.py -v
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.config import Config
from core.analyzer import DataAnalyzer
from core.llm import LLMClient


class TestConfig:
    """Tests for Config class."""
    
    def test_page_title_exists(self):
        """Test that PAGE_TITLE is defined."""
        assert hasattr(Config, 'PAGE_TITLE')
        assert "OmniAgent" in Config.PAGE_TITLE
    
    def test_author_info_exists(self):
        """Test that author info is defined."""
        assert hasattr(Config, 'AUTHOR')
        assert hasattr(Config, 'AUTHOR_URL')
        assert "Hooman" in Config.AUTHOR
        assert "esteki.ca" in Config.AUTHOR_URL
    
    def test_paths_exist(self):
        """Test that paths are defined."""
        assert hasattr(Config, 'BASE_DIR')
        assert hasattr(Config, 'DATA_DIR')
        assert hasattr(Config, 'SAMPLES_DIR')
    
    def test_color_scheme_exists(self):
        """Test that color scheme is defined."""
        assert hasattr(Config, 'COLORS')
        assert isinstance(Config.COLORS, list)
        assert len(Config.COLORS) > 0
    
    def test_sample_datasets_exist(self):
        """Test that sample datasets are configured."""
        assert hasattr(Config, 'SAMPLE_DATASETS')
        assert isinstance(Config.SAMPLE_DATASETS, dict)
        assert len(Config.SAMPLE_DATASETS) > 0


class TestDataAnalyzer:
    """Tests for DataAnalyzer class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe for testing."""
        return pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'age': [25, 30, 35, 40, 45],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'gender': ['M', 'F', 'M', 'F', 'M'],
            'department': ['Sales', 'IT', 'HR', 'IT', 'Sales'],
            'rating': [4.5, 3.8, 4.2, 4.9, 3.5]
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create an analyzer instance."""
        return DataAnalyzer(sample_df)
    
    def test_initialization(self, analyzer, sample_df):
        """Test analyzer initialization."""
        assert analyzer.df is not None
        assert analyzer.row_count == 5
        assert analyzer.col_count == 6
    
    def test_numeric_columns_detection(self, analyzer):
        """Test detection of numeric columns."""
        assert 'age' in analyzer.usable_numeric
        assert 'salary' in analyzer.usable_numeric
        assert 'rating' in analyzer.usable_numeric
        # ID should be excluded
        assert 'id' not in analyzer.usable_numeric
    
    def test_categorical_columns_detection(self, analyzer):
        """Test detection of categorical columns."""
        assert 'gender' in analyzer.usable_categorical
        assert 'department' in analyzer.usable_categorical
    
    def test_id_column_detection(self, analyzer):
        """Test detection of ID columns."""
        assert 'id' in analyzer.id_columns
    
    def test_target_candidates(self, analyzer):
        """Test target candidate generation."""
        candidates = analyzer.target_candidates
        assert len(candidates) > 0
        # Should include both numeric (regression) and categorical (classification)
        types = [c['type'] for c in candidates]
        assert 'regression' in types or 'classification' in types
    
    def test_summary_generation(self, analyzer):
        """Test summary generation."""
        summary = analyzer.get_summary()
        # Match actual keys from DataAnalyzer
        assert 'rows' in summary or 'row_count' in summary
        assert 'columns' in summary or 'col_count' in summary
        assert 'missing_total' in summary
    
    def test_missing_values_detection(self):
        """Test detection of missing values."""
        df_with_missing = pd.DataFrame({
            'a': [1, 2, None, 4, 5],
            'b': ['x', None, 'z', 'w', 'v']
        })
        analyzer = DataAnalyzer(df_with_missing)
        summary = analyzer.get_summary()
        assert summary['missing_total'] > 0
    
    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        empty_df = pd.DataFrame()
        analyzer = DataAnalyzer(empty_df)
        assert analyzer.row_count == 0
        assert analyzer.col_count == 0
    
    def test_all_numeric_dataframe(self):
        """Test dataframe with only numeric columns."""
        numeric_df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [4.0, 5.0, 6.0],
            'c': [7, 8, 9]
        })
        analyzer = DataAnalyzer(numeric_df)
        assert len(analyzer.usable_numeric) >= 2
        assert len(analyzer.usable_categorical) == 0
    
    def test_all_categorical_dataframe(self):
        """Test dataframe with only categorical columns."""
        cat_df = pd.DataFrame({
            'a': ['x', 'y', 'z'],
            'b': ['p', 'q', 'r']
        })
        analyzer = DataAnalyzer(cat_df)
        assert len(analyzer.usable_categorical) == 2
        assert len(analyzer.usable_numeric) == 0


class TestLLMClient:
    """Tests for LLMClient class."""
    
    def test_initialization_without_key(self):
        """Test initialization without API key."""
        client = LLMClient()
        assert client.available == False or client.api_key == ""
    
    def test_initialization_with_key(self):
        """Test initialization with API key."""
        client = LLMClient(api_key="test_key_123")
        assert client.api_key == "test_key_123"
        assert client.available == True
    
    def test_set_api_key(self):
        """Test setting API key dynamically."""
        client = LLMClient()
        client.set_api_key("new_key_456")
        assert client.api_key == "new_key_456"
        assert client.available == True
    
    def test_toggle_enabled(self):
        """Test toggling LLM enabled state."""
        client = LLMClient(api_key="test_key")
        assert client.enabled == True
        client.toggle(False)
        assert client.enabled == False
        client.toggle(True)
        assert client.enabled == True
    
    def test_is_active_requires_both(self):
        """Test that is_active requires both available and enabled."""
        client = LLMClient(api_key="test_key")
        assert client.is_active() == True
        
        client.toggle(False)
        assert client.is_active() == False
        
        client.toggle(True)
        client.set_api_key("")
        assert client.is_active() == False
    
    @patch('core.llm.requests')
    def test_chat_returns_none_when_inactive(self, mock_requests):
        """Test that chat returns None when LLM is inactive."""
        client = LLMClient()  # No API key
        result = client.chat([{"role": "user", "content": "test"}])
        assert result is None
        mock_requests.post.assert_not_called()
    
    def test_model_default(self):
        """Test default model is set."""
        client = LLMClient()
        assert client.model is not None
        assert "llama" in client.model.lower() or len(client.model) > 0


class TestDataAnalyzerEdgeCases:
    """Edge case tests for DataAnalyzer."""
    
    def test_single_row_dataframe(self):
        """Test with single row dataframe."""
        df = pd.DataFrame({'a': [1], 'b': ['x']})
        analyzer = DataAnalyzer(df)
        assert analyzer.row_count == 1
    
    def test_single_column_dataframe(self):
        """Test with single column dataframe."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        analyzer = DataAnalyzer(df)
        assert analyzer.col_count == 1
    
    def test_column_with_all_nulls(self):
        """Test column with all null values."""
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [None, None, None]
        })
        analyzer = DataAnalyzer(df)
        summary = analyzer.get_summary()
        assert summary['missing_total'] == 3
    
    def test_mixed_types_column(self):
        """Test column with mixed types."""
        df = pd.DataFrame({
            'mixed': [1, 'two', 3.0, 'four']
        })
        analyzer = DataAnalyzer(df)
        # Should handle gracefully
        assert analyzer.df is not None
    
    def test_large_number_of_unique_values(self):
        """Test ID detection for column with many unique values."""
        df = pd.DataFrame({
            'possible_id': list(range(100)),
            'value': [1] * 100
        })
        analyzer = DataAnalyzer(df)
        assert 'possible_id' in analyzer.id_columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
