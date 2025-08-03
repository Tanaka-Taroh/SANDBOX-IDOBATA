"""Configuration settings for Serena-MCP."""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Configuration for Serena-MCP server."""
    
    # Server settings
    SOCKET_PATH: str = os.getenv("SERENA_MCP_SOCKET", "/tmp/serena-mcp.sock")
    HOST: str = os.getenv("SERENA_MCP_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("SERENA_MCP_PORT", "9000"))
    
    # Cache settings
    CACHE_SIZE_MB: int = int(os.getenv("SERENA_MCP_CACHE_SIZE", "512"))
    CACHE_TTL_DAYS: int = int(os.getenv("SERENA_MCP_CACHE_TTL", "14"))
    
    # LSP settings
    LSP_TIMEOUT_MS: int = int(os.getenv("SERENA_MCP_LSP_TIMEOUT", "5000"))
    
    # Token settings
    MAX_TOKENS: int = int(os.getenv("SERENA_MCP_MAX_TOKENS", "4096"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("SERENA_MCP_LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("SERENA_MCP_LOG_FILE")
    
    # Development mode
    DEBUG: bool = os.getenv("SERENA_MCP_DEBUG", "false").lower() == "true"