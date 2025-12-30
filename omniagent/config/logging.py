"""
Structured logging configuration for OmniAgent.

Uses structlog for structured logging with:
- Pretty console output for development
- JSON output for production
- Context binding for tracing across agents
"""

import logging
import sys
from typing import Any

import structlog
from rich.console import Console

from omniagent.config.settings import get_settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Call this once at application startup.
    """
    settings = get_settings()
    
    # Set up standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )
    
    # Configure structlog
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if settings.debug:
        # Pretty output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        ]
    else:
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Usually __name__ of the calling module
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


# Convenience for common logging patterns
class AgentLogger:
    """
    Specialized logger for agent operations.
    
    Provides methods for common agent logging patterns with
    automatic context binding.
    """
    
    def __init__(self, agent_name: str):
        self.logger = get_logger(agent_name)
        self.agent_name = agent_name
    
    def tool_call(
        self,
        tool_name: str,
        inputs: dict[str, Any],
    ) -> None:
        """Log when a tool is called."""
        self.logger.info(
            "Tool called",
            agent=self.agent_name,
            tool=tool_name,
            inputs=inputs,
        )
    
    def tool_result(
        self,
        tool_name: str,
        success: bool,
        duration_ms: float,
        result_summary: str | None = None,
    ) -> None:
        """Log tool execution result."""
        self.logger.info(
            "Tool completed",
            agent=self.agent_name,
            tool=tool_name,
            success=success,
            duration_ms=round(duration_ms, 2),
            result=result_summary,
        )
    
    def tool_error(
        self,
        tool_name: str,
        error: Exception,
    ) -> None:
        """Log tool execution error."""
        self.logger.error(
            "Tool failed",
            agent=self.agent_name,
            tool=tool_name,
            error=str(error),
            error_type=type(error).__name__,
        )
    
    def agent_thinking(self, thought: str) -> None:
        """Log agent reasoning."""
        self.logger.debug(
            "Agent thinking",
            agent=self.agent_name,
            thought=thought,
        )
