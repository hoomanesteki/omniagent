"""
Agents Module
=============
Specialized agents for data analysis.
"""

from agents.base import BaseAgent
from agents.stats_agent import StatsAgent
from agents.viz_agent import VizAgent
from agents.predict_agent import PredictAgent
from agents.sql_agent import SQLAgent
from agents.aggregate_agent import AggregateAgent
from agents.master_agent import MasterAgent
from agents.voice_agent import VoiceAgent
from agents.dynamic_agent import DynamicAgent

__all__ = [
    'BaseAgent',
    'StatsAgent', 
    'VizAgent',
    'PredictAgent',
    'SQLAgent',
    'AggregateAgent',
    'MasterAgent',
    'VoiceAgent',
    'DynamicAgent'
]
