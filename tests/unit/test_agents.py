"""
Unit Tests for Agent Modules
============================
Tests for all specialized agents.

Run with: pytest tests/unit/test_agents.py -v
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.analyzer import DataAnalyzer


class TestBaseAgent:
    """Tests for BaseAgent class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        return pd.DataFrame({
            'id': range(1, 101),
            'age': np.random.randint(18, 65, 100),
            'salary': np.random.randint(30000, 150000, 100),
            'department': np.random.choice(['Sales', 'IT', 'HR', 'Marketing'], 100),
            'gender': np.random.choice(['M', 'F'], 100)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    def test_base_agent_abstract(self):
        """Test that BaseAgent is abstract."""
        from agents.base import BaseAgent
        # BaseAgent should have required attributes
        assert hasattr(BaseAgent, 'name')
        assert hasattr(BaseAgent, 'emoji')


class TestStatsAgent:
    """Tests for StatsAgent class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        np.random.seed(42)
        return pd.DataFrame({
            'id': range(1, 101),
            'age': np.random.randint(18, 65, 100),
            'salary': np.random.randint(30000, 150000, 100),
            'score': np.random.uniform(0, 100, 100),
            'department': np.random.choice(['Sales', 'IT', 'HR'], 100)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def stats_agent(self, sample_df, analyzer):
        """Create StatsAgent."""
        from agents.stats_agent import StatsAgent
        return StatsAgent(sample_df, analyzer)
    
    def test_stats_agent_initialization(self, stats_agent):
        """Test StatsAgent initialization."""
        assert stats_agent.name == "Stats Agent"
        assert stats_agent.emoji == "📊"
    
    def test_describe_all(self, stats_agent):
        """Test describe_all method."""
        result = stats_agent.describe_all()
        assert 'content' in result
        assert 'Stats Agent' in result['content']
    
    def test_describe_column(self, stats_agent):
        """Test describe_column method."""
        result = stats_agent.describe_column('age')
        assert 'content' in result
        assert 'age' in result['content'].lower()
    
    def test_missing_analysis(self, stats_agent):
        """Test missing values analysis."""
        result = stats_agent.missing_analysis()
        assert 'content' in result
        assert 'missing' in result['content'].lower() or 'quality' in result['content'].lower()
    
    def test_get_stat_mean(self, stats_agent):
        """Test getting mean statistic."""
        result = stats_agent.get_stat('age', 'mean')
        assert 'content' in result
        assert 'mean' in result['content'].lower() or 'average' in result['content'].lower()
    
    def test_get_stat_median(self, stats_agent):
        """Test getting median statistic."""
        result = stats_agent.get_stat('salary', 'median')
        assert 'content' in result
    
    def test_process_mean_query(self, stats_agent):
        """Test processing mean query."""
        result = stats_agent.process("what is the mean of age")
        assert 'content' in result
    
    def test_process_missing_query(self, stats_agent):
        """Test processing missing values query."""
        result = stats_agent.process("check missing values")
        assert 'content' in result
    
    def test_process_statistics_query(self, stats_agent):
        """Test processing statistics query."""
        result = stats_agent.process("show statistics")
        assert 'content' in result
    
    def test_suggestions_generated(self, stats_agent):
        """Test that suggestions are generated."""
        result = stats_agent.describe_all()
        assert 'suggestions' in result
        assert len(result['suggestions']) > 0


class TestVizAgent:
    """Tests for VizAgent class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        np.random.seed(42)
        return pd.DataFrame({
            'age': np.random.randint(18, 65, 100),
            'salary': np.random.randint(30000, 150000, 100),
            'department': np.random.choice(['Sales', 'IT', 'HR'], 100),
            'rating': np.random.uniform(1, 5, 100)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def viz_agent(self, sample_df, analyzer):
        """Create VizAgent."""
        from agents.viz_agent import VizAgent
        return VizAgent(sample_df, analyzer)
    
    def test_viz_agent_initialization(self, viz_agent):
        """Test VizAgent initialization."""
        assert viz_agent.name == "Visualization Agent"
        assert viz_agent.emoji == "📈"
    
    def test_histogram(self, viz_agent):
        """Test histogram generation."""
        result = viz_agent.histogram('age')
        assert 'content' in result
        assert 'figure' in result or result.get('figure') is not None or 'Histogram' in result['content']
    
    def test_bar(self, viz_agent):
        """Test bar chart generation."""
        result = viz_agent.bar('department')
        assert 'content' in result
    
    def test_box(self, viz_agent):
        """Test box plot generation."""
        result = viz_agent.box('salary')
        assert 'content' in result
    
    def test_heatmap(self, viz_agent):
        """Test correlation heatmap."""
        result = viz_agent.heatmap()
        assert 'content' in result
    
    def test_scatter(self, viz_agent):
        """Test scatter plot."""
        result = viz_agent.scatter('age', 'salary')
        assert 'content' in result
    
    def test_process_histogram_query(self, viz_agent):
        """Test processing histogram query."""
        result = viz_agent.process("histogram of age")
        assert 'content' in result
    
    def test_process_correlation_query(self, viz_agent):
        """Test processing correlation query."""
        result = viz_agent.process("correlation heatmap")
        assert 'content' in result


class TestAggregateAgent:
    """Tests for AggregateAgent class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        np.random.seed(42)
        return pd.DataFrame({
            'product': np.random.choice(['A', 'B', 'C'], 100),
            'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
            'sales': np.random.randint(100, 1000, 100),
            'quantity': np.random.randint(1, 50, 100)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def agg_agent(self, sample_df, analyzer):
        """Create AggregateAgent."""
        from agents.aggregate_agent import AggregateAgent
        return AggregateAgent(sample_df, analyzer)
    
    def test_agg_agent_initialization(self, agg_agent):
        """Test AggregateAgent initialization."""
        assert agg_agent.name == "Aggregate Agent"
        assert agg_agent.emoji == "📦"
    
    def test_count_by(self, agg_agent):
        """Test count by category."""
        result = agg_agent.count_by('product')
        assert 'content' in result
        assert 'count' in result['content'].lower()
    
    def test_groupby_summary(self, agg_agent):
        """Test groupby summary."""
        result = agg_agent.groupby_summary('region')
        assert 'content' in result
    
    def test_groupby_agg(self, agg_agent):
        """Test groupby aggregation."""
        result = agg_agent.groupby_agg('region', 'sales', 'sum')
        assert 'content' in result
    
    def test_process_count_query(self, agg_agent):
        """Test processing count query."""
        result = agg_agent.process("count by product")
        assert 'content' in result
    
    def test_process_sum_query(self, agg_agent):
        """Test processing sum query."""
        result = agg_agent.process("sum sales by region")
        assert 'content' in result


class TestSQLAgent:
    """Tests for SQLAgent class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        return pd.DataFrame({
            'id': range(1, 51),
            'name': [f'Item_{i}' for i in range(1, 51)],
            'value': np.random.randint(1, 100, 50)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def sql_agent(self, sample_df, analyzer):
        """Create SQLAgent."""
        from agents.sql_agent import SQLAgent
        return SQLAgent(sample_df, analyzer)
    
    def test_sql_agent_initialization(self, sql_agent):
        """Test SQLAgent initialization."""
        assert sql_agent.name == "SQL Agent"
        assert sql_agent.emoji == "🔍"
    
    def test_sample_first(self, sql_agent):
        """Test getting first rows."""
        result = sql_agent.sample(10, "first")
        assert 'content' in result
        assert 'dataframe' in result
        assert len(result['dataframe']) == 10
    
    def test_sample_last(self, sql_agent):
        """Test getting last rows."""
        result = sql_agent.sample(5, "last")
        assert 'dataframe' in result
        assert len(result['dataframe']) == 5
    
    def test_sample_random(self, sql_agent):
        """Test getting random rows."""
        result = sql_agent.sample(10, "random")
        assert 'dataframe' in result
        assert len(result['dataframe']) == 10
    
    def test_columns(self, sql_agent):
        """Test showing columns."""
        result = sql_agent.columns()
        assert 'content' in result
    
    def test_process_first_query(self, sql_agent):
        """Test processing first rows query."""
        result = sql_agent.process("show first 10 rows")
        assert 'content' in result
    
    def test_process_columns_query(self, sql_agent):
        """Test processing columns query."""
        result = sql_agent.process("show columns")
        assert 'content' in result


class TestPredictAgent:
    """Tests for PredictAgent class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe for prediction."""
        np.random.seed(42)
        n = 200
        return pd.DataFrame({
            'feature1': np.random.randn(n),
            'feature2': np.random.randn(n),
            'feature3': np.random.choice(['A', 'B', 'C'], n),
            'target_numeric': np.random.randn(n),
            'target_class': np.random.choice(['Yes', 'No'], n)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def predict_agent(self, sample_df, analyzer):
        """Create PredictAgent."""
        from agents.predict_agent import PredictAgent
        return PredictAgent(sample_df, analyzer)
    
    def test_predict_agent_initialization(self, predict_agent):
        """Test PredictAgent initialization."""
        assert predict_agent.name == "Prediction Agent"
        assert predict_agent.emoji == "🤖"
    
    def test_suggest_targets(self, predict_agent):
        """Test suggesting prediction targets."""
        result = predict_agent.suggest_targets()
        assert 'content' in result
        assert 'target' in result['content'].lower() or 'predict' in result['content'].lower()
    
    def test_process_what_predict_query(self, predict_agent):
        """Test processing what can I predict query."""
        result = predict_agent.process("what can I predict")
        assert 'content' in result
    
    def test_process_build_model_query(self, predict_agent):
        """Test processing build model query."""
        result = predict_agent.process("build model")
        assert 'content' in result


class TestMasterAgentRouting:
    """Tests for MasterAgent routing logic."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        np.random.seed(42)
        return pd.DataFrame({
            'age': np.random.randint(18, 65, 100),
            'salary': np.random.randint(30000, 150000, 100),
            'department': np.random.choice(['Sales', 'IT', 'HR'], 100),
            'gender': np.random.choice(['M', 'F'], 100)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def master_agent(self, sample_df, analyzer):
        """Create MasterAgent."""
        from agents.master_agent import MasterAgent
        return MasterAgent(sample_df, analyzer)
    
    def test_master_agent_initialization(self, master_agent):
        """Test MasterAgent initialization."""
        assert master_agent.name == "Master Agent"
        assert master_agent.emoji == "🧠"
    
    def test_detect_stats_intent(self, master_agent):
        """Test detecting stats intent."""
        intent = master_agent._detect_intent("show statistics")
        assert intent == 'stats'
    
    def test_detect_histogram_intent(self, master_agent):
        """Test detecting histogram intent."""
        intent = master_agent._detect_intent("histogram of age")
        assert intent == 'histogram'
    
    def test_detect_aggregate_intent(self, master_agent):
        """Test detecting aggregate intent."""
        intent = master_agent._detect_intent("count by department")
        assert intent == 'aggregate'
    
    def test_detect_predict_intent(self, master_agent):
        """Test detecting predict intent."""
        intent = master_agent._detect_intent("predict salary")
        assert intent == 'predict'
    
    def test_detect_help_intent(self, master_agent):
        """Test detecting help intent."""
        intent = master_agent._detect_intent("help")
        assert intent == 'help'
    
    def test_detect_about_intent(self, master_agent):
        """Test detecting about intent."""
        intent = master_agent._detect_intent("about")
        assert intent == 'about'
    
    def test_detect_refuse_intent(self, master_agent):
        """Test detecting refuse intent."""
        intent = master_agent._detect_intent("delete all rows")
        assert intent == 'refuse'
    
    def test_detect_dynamic_intent(self, master_agent):
        """Test detecting dynamic intent."""
        intent = master_agent._detect_intent("calculate rolling average of salary")
        assert intent == 'dynamic'
    
    def test_process_returns_dict(self, master_agent):
        """Test that process returns a dictionary."""
        result = master_agent.process("show statistics")
        assert isinstance(result, dict)
        assert 'content' in result
    
    def test_help_content(self, master_agent):
        """Test help content is comprehensive."""
        result = master_agent._help()
        content = result['content']
        assert 'Statistics' in content
        assert 'Visualization' in content
        assert 'Aggregation' in content
        assert 'Prediction' in content
        assert 'Dynamic' in content
    
    def test_about_content(self, master_agent):
        """Test about content."""
        result = master_agent._about()
        content = result['content']
        assert 'OmniAgent' in content
        assert 'Architecture' in content
        assert 'MCP' in content


class TestDynamicAgent:
    """Tests for DynamicAgent class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        np.random.seed(42)
        return pd.DataFrame({
            'age': np.random.randint(18, 65, 100),
            'salary': np.random.randint(30000, 150000, 100),
            'department': np.random.choice(['Sales', 'IT', 'HR'], 100)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        """Create analyzer."""
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def dynamic_agent(self, analyzer):
        """Create DynamicAgent."""
        from agents.dynamic_agent import DynamicAgent
        return DynamicAgent(analyzer=analyzer, llm=None)
    
    def test_dynamic_agent_initialization(self, dynamic_agent):
        """Test DynamicAgent initialization."""
        assert dynamic_agent.name == "Dynamic Agent"
        assert dynamic_agent.emoji == "🔮"
    
    def test_detect_rolling_category(self, dynamic_agent):
        """Test detecting rolling category."""
        category = dynamic_agent._detect_category("rolling average of salary")
        assert category == 'rolling'
    
    def test_detect_outlier_category(self, dynamic_agent):
        """Test detecting outlier category."""
        category = dynamic_agent._detect_category("find outliers in age")
        assert category == 'outlier'
    
    def test_detect_regression_category(self, dynamic_agent):
        """Test detecting regression category."""
        category = dynamic_agent._detect_category("scatter plot with regression line")
        assert category == 'regression'
    
    def test_detect_binning_category(self, dynamic_agent):
        """Test detecting binning category."""
        category = dynamic_agent._detect_category("bin age into categories")
        assert category == 'binning'
    
    def test_is_confirmation_yes(self, dynamic_agent):
        """Test yes confirmation detection."""
        assert dynamic_agent._is_confirmation("yes") == True
        assert dynamic_agent._is_confirmation("y") == True
        assert dynamic_agent._is_confirmation("ok") == True
        assert dynamic_agent._is_confirmation("go ahead") == True
    
    def test_is_confirmation_no(self, dynamic_agent):
        """Test no confirmation detection."""
        assert dynamic_agent._is_confirmation("no") == False
        assert dynamic_agent._is_confirmation("n") == False
        assert dynamic_agent._is_confirmation("cancel") == False
        assert dynamic_agent._is_confirmation("stop") == False
    
    def test_is_confirmation_other(self, dynamic_agent):
        """Test non-confirmation detection."""
        # Long queries should return None (not a simple confirmation)
        assert dynamic_agent._is_confirmation("calculate the rolling average of all columns in the dataset") is None
        # Short queries with confirmation words return True/False, not None
        # The function only returns None for long non-confirmation queries
    
    def test_code_safety_blocks_os(self, dynamic_agent):
        """Test that os import is blocked."""
        is_safe, msg = dynamic_agent._is_code_safe("import os\nos.system('ls')")
        assert is_safe == False
    
    def test_code_safety_blocks_eval(self, dynamic_agent):
        """Test that eval is blocked."""
        is_safe, msg = dynamic_agent._is_code_safe("eval('print(1)')")
        assert is_safe == False
    
    def test_code_safety_blocks_exec(self, dynamic_agent):
        """Test that exec is blocked."""
        is_safe, msg = dynamic_agent._is_code_safe("exec('print(1)')")
        assert is_safe == False
    
    def test_code_safety_blocks_open(self, dynamic_agent):
        """Test that open is blocked."""
        is_safe, msg = dynamic_agent._is_code_safe("open('/etc/passwd', 'r')")
        assert is_safe == False
    
    def test_code_safety_allows_pandas(self, dynamic_agent):
        """Test that pandas operations are allowed."""
        code = """
import pandas as pd
result = df['age'].mean()
"""
        is_safe, msg = dynamic_agent._is_code_safe(code)
        assert is_safe == True
    
    def test_code_safety_allows_numpy(self, dynamic_agent):
        """Test that numpy operations are allowed."""
        code = """
import numpy as np
result = np.mean(df['age'])
"""
        is_safe, msg = dynamic_agent._is_code_safe(code)
        assert is_safe == True
    
    def test_code_safety_blocks_subprocess(self, dynamic_agent):
        """Test that subprocess is blocked."""
        is_safe, msg = dynamic_agent._is_code_safe("import subprocess")
        assert is_safe == False
    
    def test_code_safety_blocks_socket(self, dynamic_agent):
        """Test that socket is blocked."""
        is_safe, msg = dynamic_agent._is_code_safe("import socket")
        assert is_safe == False
    
    def test_code_length_limit(self, dynamic_agent):
        """Test code length limit."""
        long_code = "x = 1\n" * 10000
        is_safe, msg = dynamic_agent._is_code_safe(long_code)
        assert is_safe == False
        assert "too long" in msg.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
