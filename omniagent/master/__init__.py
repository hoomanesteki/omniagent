"""
Master Agent - Orchestrates all specialized agents.

The Master Agent:
- Understands user intent
- Routes to appropriate agents
- Synthesizes final responses
"""

from omniagent.master.agent import MasterAgent
from omniagent.master.prompts import SYSTEM_PROMPT

__all__ = [
    "MasterAgent",
    "SYSTEM_PROMPT",
]
