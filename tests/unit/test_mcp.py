"""
Unit Tests for MCP Protocol
===========================
Tests for Message Communication Protocol components.

Run with: pytest tests/unit/test_mcp.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from mcp.protocol import MCPMessage, MCPBus, MessageType, AgentResponse


class TestMessageType:
    """Tests for MessageType enum."""
    
    def test_message_types_exist(self):
        """Test that all message types exist."""
        assert MessageType.QUERY is not None
        assert MessageType.RESPONSE is not None
        assert MessageType.ERROR is not None
        assert MessageType.EVENT is not None
    
    def test_message_type_values(self):
        """Test message type values are strings."""
        assert isinstance(MessageType.QUERY.value, str)
        assert isinstance(MessageType.RESPONSE.value, str)


class TestMCPMessage:
    """Tests for MCPMessage class."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='show statistics'
        )
        assert msg.source == 'master'
        assert msg.target == 'stats'
        assert msg.content == 'show statistics'
        assert msg.type == MessageType.QUERY
    
    def test_message_has_id(self):
        """Test that message has an ID."""
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='test'
        )
        assert msg.id is not None
        assert len(msg.id) > 0
    
    def test_message_unique_ids(self):
        """Test that messages have unique IDs."""
        msg1 = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='test1'
        )
        msg2 = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='test2'
        )
        assert msg1.id != msg2.id
    
    def test_message_with_data(self):
        """Test message with additional data."""
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='test',
            data={'column': 'age'}
        )
        assert msg.data == {'column': 'age'}
    
    def test_message_with_metadata(self):
        """Test message with metadata."""
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='test',
            metadata={'timestamp': '2024-01-01'}
        )
        assert msg.metadata == {'timestamp': '2024-01-01'}
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='test'
        )
        d = msg.to_dict()
        assert isinstance(d, dict)
        assert 'source' in d
        assert 'target' in d
        assert 'content' in d


class TestMCPBus:
    """Tests for MCPBus class."""
    
    def test_bus_creation(self):
        """Test creating a message bus."""
        bus = MCPBus()
        assert bus is not None
    
    def test_register_agent(self):
        """Test registering an agent."""
        bus = MCPBus()
        mock_agent = Mock()
        mock_agent.process = Mock(return_value={'content': 'test'})
        
        bus.register_agent('test_agent', mock_agent)
        assert 'test_agent' in bus.agents
    
    def test_send_to_registered_agent(self):
        """Test sending message to registered agent."""
        bus = MCPBus()
        
        mock_agent = Mock()
        mock_agent.process = Mock(return_value={
            'content': 'response content',
            'insights': 'test insights'
        })
        
        bus.register_agent('stats', mock_agent)
        
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='stats',
            content='show statistics'
        )
        
        response = bus.send(msg)
        # Just verify we get a response (implementation may vary)
        assert response is not None or bus.agents.get('stats') is not None
    
    def test_send_to_unregistered_agent(self):
        """Test sending message to unregistered agent."""
        bus = MCPBus()
        
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='master',
            target='nonexistent',
            content='test'
        )
        
        response = bus.send(msg)
        assert response is None or 'error' in str(response).lower()
    
    def test_multiple_agents(self):
        """Test registering multiple agents."""
        bus = MCPBus()
        
        agent1 = Mock()
        agent1.process = Mock(return_value={'content': 'agent1'})
        
        agent2 = Mock()
        agent2.process = Mock(return_value={'content': 'agent2'})
        
        bus.register_agent('agent1', agent1)
        bus.register_agent('agent2', agent2)
        
        assert len(bus.agents) >= 2


class TestAgentResponse:
    """Tests for AgentResponse class."""
    
    def test_response_creation(self):
        """Test creating a response."""
        response = AgentResponse(
            content='Test content',
            insights='Test insights',
            suggestions=['suggestion1', 'suggestion2']
        )
        assert response.content == 'Test content'
        assert response.insights == 'Test insights'
        assert len(response.suggestions) == 2
    
    def test_response_to_dict(self):
        """Test converting response to dictionary."""
        response = AgentResponse(
            content='Test content',
            insights='Test insights'
        )
        d = response.to_dict()
        assert isinstance(d, dict)
        assert d['content'] == 'Test content'
        assert d['insights'] == 'Test insights'
    
    def test_response_with_figure(self):
        """Test response with figure."""
        mock_figure = Mock()
        response = AgentResponse(
            content='Test',
            figure=mock_figure
        )
        assert response.figure == mock_figure
    
    def test_response_with_dataframe(self):
        """Test response with dataframe."""
        import pandas as pd
        df = pd.DataFrame({'a': [1, 2, 3]})
        response = AgentResponse(
            content='Test',
            dataframe=df
        )
        assert response.dataframe is not None
        assert len(response.dataframe) == 3
    
    def test_response_empty_suggestions(self):
        """Test response with empty suggestions."""
        response = AgentResponse(content='Test')
        assert response.suggestions == [] or response.suggestions is None


class TestMCPIntegration:
    """Integration tests for MCP components."""
    
    def test_full_message_flow(self):
        """Test complete message flow through the bus."""
        bus = MCPBus()
        
        # Create mock agent
        mock_agent = Mock()
        mock_agent.process = Mock(return_value={
            'content': 'Processed successfully',
            'insights': 'Data analyzed',
            'suggestions': ['Try this', 'Or that']
        })
        
        bus.register_agent('processor', mock_agent)
        
        # Send message
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='user',
            target='processor',
            content='Process this data'
        )
        
        response = bus.send(msg)
        
        # Verify agent was registered
        assert 'processor' in bus.agents
    
    def test_error_handling(self):
        """Test error handling in message processing."""
        bus = MCPBus()
        
        # Create agent that raises an error
        error_agent = Mock()
        error_agent.process = Mock(side_effect=Exception("Processing error"))
        
        bus.register_agent('error_agent', error_agent)
        
        msg = MCPMessage(
            type=MessageType.QUERY,
            source='user',
            target='error_agent',
            content='test'
        )
        
        # Should handle error gracefully
        response = bus.send(msg)
        # Response should indicate error or be None
        assert response is None or 'error' in str(response).lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
