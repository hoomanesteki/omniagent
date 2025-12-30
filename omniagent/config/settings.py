"""
Application settings management using Pydantic.

This module provides:
- Type-safe configuration loading from environment variables
- Validation of all settings at startup
- Sensible defaults for development
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables.
    Example: LLM_MODEL=claude-sonnet-4-20250514
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ----- LLM Configuration -----
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude access",
    )
    llm_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model to use for LLM calls",
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens in LLM response",
    )
    llm_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="LLM temperature (0=deterministic, 1=creative)",
    )
    
    # ----- Application Settings -----
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    
    # ----- Data Settings -----
    max_upload_size_mb: int = Field(
        default=100,
        description="Maximum file upload size in MB",
    )
    max_rows_display: int = Field(
        default=1000,
        description="Maximum rows to display in results",
    )
    sql_timeout_seconds: int = Field(
        default=30,
        description="Timeout for SQL queries",
    )
    
    # ----- Data Storage Paths -----
    data_dir: str = Field(
        default="data",
        description="Directory for data storage",
    )
    uploads_dir: str = Field(
        default="data/uploads",
        description="Directory for file uploads",
    )
    
    # ----- MCP Settings -----
    mcp_transport: Literal["stdio", "sse"] = Field(
        default="stdio",
        description="MCP transport type",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
