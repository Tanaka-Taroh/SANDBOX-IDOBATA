"""MCP Server implementation for Serena-MCP."""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .config import Config
from .context_manager import ContextManager
from .lsp_client import LSPClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ContextRequest(BaseModel):
    """Request model for context retrieval."""
    query: str
    scope: str = "function"  # function, class, file, project
    max_tokens: int = Config.MAX_TOKENS


class ContextResponse(BaseModel):
    """Response model for context retrieval."""
    symbols: list[Dict[str, Any]]
    dependencies: list[Dict[str, str]]
    references: list[Dict[str, Any]]
    tokens_saved: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting Serena-MCP server...")
    app.state.lsp_client = LSPClient()
    app.state.context_manager = ContextManager(app.state.lsp_client)
    
    # Initialize LSP connections
    await app.state.lsp_client.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Serena-MCP server...")
    await app.state.lsp_client.shutdown()


app = FastAPI(
    title="Serena-MCP",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/mcp/v1/context", response_model=ContextResponse)
async def get_context(request: ContextRequest):
    """Get context for the given query."""
    try:
        context = await app.state.context_manager.get_context(
            query=request.query,
            scope=request.scope,
            max_tokens=request.max_tokens,
        )
        return context
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Remove existing socket if it exists
    socket_path = Path(Config.SOCKET_PATH)
    if socket_path.exists():
        socket_path.unlink()
    
    # Run server
    if Config.DEBUG:
        # HTTP mode for debugging
        uvicorn.run(
            "serena_mcp.mcp_server:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=True,
        )
    else:
        # Unix socket mode for production
        uvicorn.run(
            app,
            uds=Config.SOCKET_PATH,
            log_level=Config.LOG_LEVEL.lower(),
        )


if __name__ == "__main__":
    main()