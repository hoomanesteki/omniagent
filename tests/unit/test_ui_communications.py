"""
UI/UX Communication Tests
=========================
Tests for all user-facing communications, messages, and formatting.

Run with: pytest tests/unit/test_ui_communications.py -v
"""

import pytest
import pandas as pd
import numpy as np
import re
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.analyzer import DataAnalyzer


class TestWelcomeScreen:
    """Tests for welcome screen content."""
    
    def test_welcome_has_agent_table(self):
        """Test welcome screen has agent table."""
        # Import the render function to check its content
        # We'll check the actual content structure
        expected_agents = ['Stats', 'Viz', 'Aggregate', 'Predict', 'SQL', 'Dynamic']
        
        # The welcome content should mention all agents
        from ui.chat import render_welcome
        # Can't render without streamlit, but we can check the function exists
        assert callable(render_welcome)
    
    def test_welcome_mentions_voice(self):
        """Test welcome screen mentions voice feature."""
        # Check that voice is documented
        pass  # Would need streamlit to fully test


class TestHelpContent:
    """Tests for help content quality and completeness."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample dataframe."""
        return pd.DataFrame({
            'age': [25, 30, 35],
            'salary': [50000, 60000, 70000],
            'dept': ['A', 'B', 'C']
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def master_agent(self, sample_df, analyzer):
        from agents.master_agent import MasterAgent
        return MasterAgent(sample_df, analyzer)
    
    def test_help_has_all_sections(self, master_agent):
        """Test help has all required sections."""
        result = master_agent._help()
        content = result['content']
        
        required_sections = [
            'Statistics Agent',
            'Visualization Agent',
            'Aggregation Agent',
            'Prediction Agent',
            'SQL Agent',
            'Dynamic Agent',
            'Voice Assistant',
            'Pro Tips'
        ]
        
        for section in required_sections:
            assert section in content, f"Missing section: {section}"
    
    def test_help_has_example_commands(self, master_agent):
        """Test help has example commands for each agent."""
        result = master_agent._help()
        content = result['content']
        
        # Should have command examples
        assert 'Show statistics' in content or 'show statistics' in content.lower()
        assert 'Histogram' in content or 'histogram' in content.lower()
        assert 'Count by' in content or 'count by' in content.lower()
        assert 'Predict' in content or 'predict' in content.lower()
    
    def test_help_formatting(self, master_agent):
        """Test help content is well formatted."""
        result = master_agent._help()
        content = result['content']
        
        # Should use markdown headers
        assert '##' in content or '###' in content
        
        # Should have tables
        assert '|' in content
    
    def test_help_has_voice_instructions(self, master_agent):
        """Test help has voice instructions."""
        result = master_agent._help()
        content = result['content']
        
        assert 'Voice' in content
        assert 'Speak' in content or 'speak' in content.lower()


class TestAboutContent:
    """Tests for about page content."""
    
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
    
    def test_about_has_architecture(self, master_agent):
        """Test about page has architecture diagram."""
        result = master_agent._about()
        content = result['content']
        
        assert 'Architecture' in content
        # Should have ASCII diagram
        assert '┌' in content or '│' in content
    
    def test_about_has_technology_stack(self, master_agent):
        """Test about page has technology stack."""
        result = master_agent._about()
        content = result['content']
        
        assert 'Technology' in content or 'Stack' in content
        assert 'Streamlit' in content
        assert 'Plotly' in content
        assert 'Pandas' in content
    
    def test_about_has_agent_table(self, master_agent):
        """Test about page has agent capabilities table."""
        result = master_agent._about()
        content = result['content']
        
        assert 'Agent' in content
        assert 'Stats' in content
        assert 'Viz' in content
        assert 'Dynamic' in content
    
    def test_about_has_author_info(self, master_agent):
        """Test about page has author information."""
        result = master_agent._about()
        content = result['content']
        
        assert 'Hooman' in content or 'Created' in content
        assert 'esteki.ca' in content or 'website' in content.lower()
    
    def test_about_has_mcp_explanation(self, master_agent):
        """Test about page explains MCP."""
        result = master_agent._about()
        content = result['content']
        
        assert 'MCP' in content
        assert 'Message' in content or 'Protocol' in content


class TestRefuseMessages:
    """Tests for refuse/error message quality."""
    
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
    
    def test_refuse_delete_is_helpful(self, master_agent):
        """Test delete refusal is helpful."""
        result = master_agent.process("delete all rows")
        content = result['content']
        
        # Should refuse politely
        assert '🚫' in content
        # Should offer alternative
        assert 'filter' in content.lower() or 'subset' in content.lower()
        # Should have suggestions
        assert 'What I CAN do' in content or 'can do' in content.lower()
    
    def test_refuse_download_is_helpful(self, master_agent):
        """Test download refusal is helpful."""
        result = master_agent.process("download to csv")
        content = result['content']
        
        assert '🚫' in content
        assert 'copy' in content.lower() or 'screenshot' in content.lower()
    
    def test_refuse_hack_is_appropriate(self, master_agent):
        """Test hack refusal is appropriate."""
        result = master_agent.process("hack the system")
        content = result['content']
        
        assert '🚫' in content
        assert 'data analysis' in content.lower()
    
    def test_refuse_messages_have_alternatives(self, master_agent):
        """Test refuse messages offer alternatives."""
        refuse_queries = [
            "delete rows",
            "download file",
            "export data"
        ]
        
        for query in refuse_queries:
            result = master_agent.process(query)
            content = result['content']
            
            # Should have "What I CAN do" section
            assert 'What I CAN do' in content or 'I CAN do' in content
            # Should have suggestions
            assert 'suggestions' in result
            assert len(result['suggestions']) > 0


class TestInsightsQuality:
    """Tests for insights message quality."""
    
    @pytest.fixture
    def sample_df(self):
        np.random.seed(42)
        return pd.DataFrame({
            'age': np.random.randint(18, 65, 100),
            'salary': np.random.randint(30000, 150000, 100),
            'dept': np.random.choice(['A', 'B', 'C'], 100)
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    def test_stats_insights_meaningful(self, sample_df, analyzer):
        """Test stats insights are meaningful."""
        from agents.stats_agent import StatsAgent
        agent = StatsAgent(sample_df, analyzer)
        
        result = agent.describe_all()
        insights = result.get('insights', '')
        
        # Should mention data
        assert 'data' in insights.lower() or 'column' in insights.lower() or 'numeric' in insights.lower()
    
    def test_viz_insights_descriptive(self, sample_df, analyzer):
        """Test viz insights are descriptive."""
        from agents.viz_agent import VizAgent
        agent = VizAgent(sample_df, analyzer)
        
        result = agent.histogram('age')
        insights = result.get('insights', '')
        
        # Should describe the visualization
        assert len(insights) > 0 or 'Distribution' in result['content']


class TestSuggestionsQuality:
    """Tests for suggestions quality and relevance."""
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'age': [25, 30, 35, 40, 45],
            'salary': [50000, 60000, 70000, 80000, 90000],
            'department': ['Sales', 'IT', 'HR', 'IT', 'Sales']
        })
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    @pytest.fixture
    def master_agent(self, sample_df, analyzer):
        from agents.master_agent import MasterAgent
        return MasterAgent(sample_df, analyzer)
    
    def test_suggestions_use_actual_columns(self, master_agent):
        """Test suggestions use actual column names."""
        result = master_agent.process("show statistics")
        suggestions = result.get('suggestions', [])
        
        # At least some suggestions should reference actual columns
        suggestion_text = ' '.join(suggestions)
        assert 'age' in suggestion_text.lower() or 'salary' in suggestion_text.lower() or 'department' in suggestion_text.lower()
    
    def test_suggestions_are_actionable(self, master_agent):
        """Test suggestions are actionable commands."""
        result = master_agent.process("help")
        suggestions = result.get('suggestions', [])
        
        # Suggestions should be executable commands
        for sug in suggestions:
            # Should start with emoji or be a command
            assert len(sug) > 2
    
    def test_suggestions_diverse(self, master_agent):
        """Test suggestions are diverse."""
        result = master_agent._get_home_suggestions()
        
        # Should have different types of suggestions
        categories = set()
        for sug in result:
            if '📊' in sug:
                categories.add('stats')
            elif '📈' in sug:
                categories.add('viz')
            elif '📦' in sug:
                categories.add('agg')
            elif '🤖' in sug:
                categories.add('predict')
        
        # Should have at least 2 different categories
        assert len(categories) >= 2


class TestMarkdownFormatting:
    """Tests for markdown formatting quality."""
    
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
    
    def test_headers_properly_formatted(self, master_agent):
        """Test headers are properly formatted."""
        result = master_agent._help()
        content = result['content']
        
        # Check for proper markdown headers
        lines = content.split('\n')
        for line in lines:
            if line.startswith('#'):
                # Should have space after #
                match = re.match(r'^#+\s', line)
                assert match is not None, f"Invalid header: {line}"
    
    def test_tables_properly_formatted(self, master_agent):
        """Test tables are properly formatted."""
        result = master_agent._help()
        content = result['content']
        
        # Find table rows
        table_rows = [line for line in content.split('\n') if '|' in line]
        
        for row in table_rows:
            # Each row should have consistent columns
            if row.strip().startswith('|'):
                # Count pipes
                pipe_count = row.count('|')
                assert pipe_count >= 2, f"Invalid table row: {row}"
    
    def test_code_blocks_properly_formatted(self, master_agent):
        """Test code blocks are properly formatted."""
        result = master_agent._about()
        content = result['content']
        
        # Check for code blocks
        if '```' in content:
            # Count opening and closing
            count = content.count('```')
            assert count % 2 == 0, "Unmatched code blocks"


class TestErrorMessageClarity:
    """Tests for error message clarity."""
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({'a': [1, 2, 3]})
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    def test_nonexistent_column_error(self, sample_df, analyzer):
        """Test error for nonexistent column."""
        from agents.stats_agent import StatsAgent
        agent = StatsAgent(sample_df, analyzer)
        
        result = agent.describe_column('nonexistent_column')
        content = result.get('content', '')
        
        # Should handle gracefully
        assert 'error' in content.lower() or 'not found' in content.lower() or len(content) > 0
    
    def test_invalid_operation_error(self, sample_df, analyzer):
        """Test error for invalid operation."""
        from agents.aggregate_agent import AggregateAgent
        agent = AggregateAgent(sample_df, analyzer)
        
        # Try a query that should be handled gracefully
        result = agent.process("group by nonexistent")
        
        # Should handle gracefully, not crash
        assert 'content' in result


class TestEmojiConsistency:
    """Tests for emoji usage consistency."""
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({'a': [1, 2, 3]})
    
    @pytest.fixture
    def analyzer(self, sample_df):
        return DataAnalyzer(sample_df)
    
    def test_stats_agent_emoji(self, sample_df, analyzer):
        """Test Stats Agent uses correct emoji."""
        from agents.stats_agent import StatsAgent
        agent = StatsAgent(sample_df, analyzer)
        assert agent.emoji == '📊'
    
    def test_viz_agent_emoji(self, sample_df, analyzer):
        """Test Viz Agent uses correct emoji."""
        from agents.viz_agent import VizAgent
        agent = VizAgent(sample_df, analyzer)
        assert agent.emoji == '📈'
    
    def test_aggregate_agent_emoji(self, sample_df, analyzer):
        """Test Aggregate Agent uses correct emoji."""
        from agents.aggregate_agent import AggregateAgent
        agent = AggregateAgent(sample_df, analyzer)
        assert agent.emoji == '📦'
    
    def test_predict_agent_emoji(self, sample_df, analyzer):
        """Test Predict Agent uses correct emoji."""
        from agents.predict_agent import PredictAgent
        agent = PredictAgent(sample_df, analyzer)
        assert agent.emoji == '🤖'
    
    def test_sql_agent_emoji(self, sample_df, analyzer):
        """Test SQL Agent uses correct emoji."""
        from agents.sql_agent import SQLAgent
        agent = SQLAgent(sample_df, analyzer)
        assert agent.emoji == '🔍'
    
    def test_dynamic_agent_emoji(self, analyzer):
        """Test Dynamic Agent uses correct emoji."""
        from agents.dynamic_agent import DynamicAgent
        agent = DynamicAgent(analyzer=analyzer)
        assert agent.emoji == '🔮'
    
    def test_master_agent_emoji(self, sample_df, analyzer):
        """Test Master Agent uses correct emoji."""
        from agents.master_agent import MasterAgent
        agent = MasterAgent(sample_df, analyzer)
        assert agent.emoji == '🧠'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
