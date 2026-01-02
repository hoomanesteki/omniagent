"""
Security Tests
==============
Tests for security measures and safe operation.

Run with: pytest tests/unit/test_security.py -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.analyzer import DataAnalyzer


class TestDynamicAgentSecurity:
    """Security tests for Dynamic Agent code execution."""
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def dynamic_agent(self, analyzer):
        from agents.dynamic_agent import DynamicAgent
        return DynamicAgent(analyzer=analyzer, llm=None)
    
    # System Access Tests
    def test_blocks_os_import(self, dynamic_agent):
        """Test blocking of os module import."""
        codes = [
            "import os",
            "import  os",
            "from os import system",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_sys_import(self, dynamic_agent):
        """Test blocking of sys module import."""
        codes = [
            "import sys",
            "from sys import exit",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_subprocess(self, dynamic_agent):
        """Test blocking of subprocess module."""
        codes = [
            "import subprocess",
            "subprocess.call(['ls'])",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # Code Injection Tests
    def test_blocks_eval(self, dynamic_agent):
        """Test blocking of eval function."""
        codes = [
            "eval('1+1')",
            "eval(user_input)",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_exec(self, dynamic_agent):
        """Test blocking of exec function."""
        codes = [
            "exec('print(1)')",
            "exec(code_string)",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_import_function(self, dynamic_agent):
        """Test blocking of __import__ function."""
        codes = [
            "__import__('os')",
            "__import__('subprocess')",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # File System Tests
    def test_blocks_open(self, dynamic_agent):
        """Test blocking of open function."""
        codes = [
            "open('/etc/passwd')",
            "open('file.txt', 'w')",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_file_write(self, dynamic_agent):
        """Test blocking of file write operations."""
        codes = [
            "f.write('data')",
            "file.write(content)",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # Network Tests
    def test_blocks_requests(self, dynamic_agent):
        """Test blocking of requests library."""
        codes = [
            "requests.get('http://example.com')",
            "requests.post(url, data)",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_socket(self, dynamic_agent):
        """Test blocking of socket module."""
        codes = [
            "import socket",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # Serialization Tests
    def test_blocks_pickle(self, dynamic_agent):
        """Test blocking of pickle module."""
        codes = [
            "import pickle",
            "pickle.loads(data)",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # Reflection Tests
    def test_blocks_globals(self, dynamic_agent):
        """Test blocking of globals function."""
        codes = [
            "globals()",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_getattr(self, dynamic_agent):
        """Test blocking of getattr function."""
        codes = [
            "getattr(obj, 'method')",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # Dunder Method Tests
    def test_blocks_builtins_access(self, dynamic_agent):
        """Test blocking of __builtins__ access."""
        codes = [
            "__builtins__",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_class_access(self, dynamic_agent):
        """Test blocking of __class__ access."""
        codes = [
            "obj.__class__",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    def test_blocks_subclasses(self, dynamic_agent):
        """Test blocking of __subclasses__ access."""
        codes = [
            "obj.__subclasses__()",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # Debugging Tests
    def test_blocks_breakpoint(self, dynamic_agent):
        """Test blocking of breakpoint function."""
        codes = [
            "breakpoint()",
        ]
        for code in codes:
            is_safe, _ = dynamic_agent._is_code_safe(code)
            assert is_safe == False, f"Should block: {code}"
    
    # Code Length Test
    def test_blocks_excessive_length(self, dynamic_agent):
        """Test blocking of excessively long code."""
        long_code = "x = 1\n" * 10000
        is_safe, msg = dynamic_agent._is_code_safe(long_code)
        assert is_safe == False
        assert "too long" in msg.lower()
    
    # Allowed Operations Tests
    def test_allows_pandas_operations(self, dynamic_agent):
        """Test that normal pandas operations are allowed."""
        codes = [
            "import pandas as pd",
            "result = df['a'].mean()",
            "result_df = df.head(10)",
        ]
        for code in codes:
            is_safe, msg = dynamic_agent._is_code_safe(code)
            assert is_safe == True, f"Should allow: {code}, but got: {msg}"
    
    def test_allows_numpy_operations(self, dynamic_agent):
        """Test that normal numpy operations are allowed."""
        codes = [
            "import numpy as np",
            "result = np.mean([1,2,3])",
        ]
        for code in codes:
            is_safe, msg = dynamic_agent._is_code_safe(code)
            assert is_safe == True, f"Should allow: {code}, but got: {msg}"
    
    def test_allows_plotly_operations(self, dynamic_agent):
        """Test that plotly operations are allowed."""
        codes = [
            "import plotly.express as px",
            "fig = px.histogram(df, x='a')",
        ]
        for code in codes:
            is_safe, msg = dynamic_agent._is_code_safe(code)
            assert is_safe == True, f"Should allow: {code}, but got: {msg}"


class TestMasterAgentSecurityRouting:
    """Tests for security routing in Master Agent."""
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({'a': [1, 2, 3]})
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def master_agent(self, sample_df, analyzer):
        from agents.master_agent import MasterAgent
        return MasterAgent(sample_df, analyzer)
    
    def test_refuses_delete_requests(self, master_agent):
        """Test refusal of delete requests."""
        queries = [
            "delete all rows",
            "delete rows where a > 1",
        ]
        for query in queries:
            intent = master_agent._detect_intent(query.lower())
            assert intent == 'refuse', f"Should refuse: {query}"
    
    def test_refuses_download_requests(self, master_agent):
        """Test refusal of download requests."""
        queries = [
            "download the data",
            "download to csv",
        ]
        for query in queries:
            intent = master_agent._detect_intent(query.lower())
            assert intent == 'refuse', f"Should refuse: {query}"
    
    def test_refuses_hack_requests(self, master_agent):
        """Test refusal of hack requests."""
        queries = [
            "hack the system",
            "inject code",
        ]
        for query in queries:
            intent = master_agent._detect_intent(query.lower())
            assert intent == 'refuse', f"Should refuse: {query}"


class TestInputSanitization:
    """Tests for input sanitization."""
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({'a': [1, 2, 3]})
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    def test_handles_empty_query(self, sample_df, analyzer):
        """Test handling of empty query."""
        from agents.master_agent import MasterAgent
        agent = MasterAgent(sample_df, analyzer)
        
        result = agent.process("")
        assert 'content' in result
    
    def test_handles_special_characters(self, sample_df, analyzer):
        """Test handling of special characters in query."""
        from agents.master_agent import MasterAgent
        agent = MasterAgent(sample_df, analyzer)
        
        special_queries = [
            "show <script>alert('xss')</script> statistics",
            "mean of column'; DROP TABLE users;--",
        ]
        
        for query in special_queries:
            result = agent.process(query)
            assert 'content' in result


class TestDataIsolation:
    """Tests for data isolation during operations."""
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'a': [1, 2, 3, 4, 5],
            'b': [10, 20, 30, 40, 50]
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    def test_original_data_unchanged_after_stats(self, sample_df, analyzer):
        """Test original data unchanged after stats operations."""
        original_shape = sample_df.shape
        original_sum = sample_df['a'].sum()
        
        from agents.stats_agent import StatsAgent
        agent = StatsAgent(sample_df, analyzer)
        agent.describe_all()
        
        assert sample_df.shape == original_shape
        assert sample_df['a'].sum() == original_sum
    
    def test_original_data_unchanged_after_viz(self, sample_df, analyzer):
        """Test original data unchanged after viz operations."""
        original_shape = sample_df.shape
        
        from agents.viz_agent import VizAgent
        agent = VizAgent(sample_df, analyzer)
        agent.histogram('a')
        
        assert sample_df.shape == original_shape


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
