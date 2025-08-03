"""Main entry point for serena_mcp package."""

import asyncio
import sys
from .mcp_server import main as fastapi_main
from .mcp_stdio_server import main as stdio_main

if __name__ == "__main__":
    # Check if running as MCP stdio server
    if "--stdio" in sys.argv or "MCP" in sys.argv[0]:
        asyncio.run(stdio_main())
    else:
        # Default to FastAPI server
        asyncio.run(fastapi_main())