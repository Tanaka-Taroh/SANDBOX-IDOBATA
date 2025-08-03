#!/usr/bin/env python3
"""MCP stdio server wrapper for Serena-MCP."""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

from .cache_manager import CacheManager
from .config import Config
from .context_manager import ContextManager
from .lsp_client import LSPClient

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr  # Log to stderr to keep stdout clean for JSON-RPC
)
logger = logging.getLogger(__name__)


class MCPStdioServer:
    """MCP stdio server implementation."""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.lsp_client = LSPClient()
        self.context_manager = ContextManager(self.lsp_client)
        self.request_id_counter = 0
        
    async def initialize(self):
        """Initialize the server components."""
        await self.lsp_client.initialize()
        logger.info("Serena MCP stdio server initialized")
        
    async def shutdown(self):
        """Shutdown the server components."""
        await self.lsp_client.shutdown()
        logger.info("Serena MCP stdio server shutdown")
        
    def write_response(self, response: Dict[str, Any]):
        """Write JSON-RPC response to stdout."""
        response_str = json.dumps(response)
        sys.stdout.write(f"{response_str}\n")
        sys.stdout.flush()
        
    async def handle_request(self, request: Dict[str, Any]):
        """Handle JSON-RPC request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {
                        "tools": {
                            "find_symbol": {
                                "description": "Find symbol definitions across the codebase",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "symbol_name": {"type": "string"},
                                        "language": {"type": "string"}
                                    },
                                    "required": ["symbol_name"]
                                }
                            },
                            "get_context": {
                                "description": "Get context for a specific file or symbol",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string"}
                                    },
                                    "required": ["query"]
                                }
                            },
                            "apply_edit": {
                                "description": "Apply semantic edits to code",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string"},
                                        "edits": {"type": "array"}
                                    },
                                    "required": ["file_path", "edits"]
                                }
                            }
                        }
                    },
                    "serverInfo": {
                        "name": "serena-mcp",
                        "version": "1.0.0"
                    }
                }
                
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_params = params.get("arguments", {})
                
                if tool_name == "find_symbol":
                    result = await self.context_manager.find_symbol(
                        tool_params.get("symbol_name"),
                        tool_params.get("language")
                    )
                elif tool_name == "get_context":
                    result = await self.context_manager.get_context(
                        tool_params.get("query")
                    )
                elif tool_name == "apply_edit":
                    result = await self.context_manager.apply_edit(
                        tool_params.get("file_path"),
                        tool_params.get("edits")
                    )
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
                    
            elif method == "tools/list":
                result = {
                    "tools": [
                        {
                            "name": "find_symbol",
                            "description": "Find symbol definitions across the codebase",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "symbol_name": {"type": "string"},
                                    "language": {"type": "string"}
                                },
                                "required": ["symbol_name"]
                            }
                        },
                        {
                            "name": "get_context",
                            "description": "Get context for a specific file or symbol",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"}
                                },
                                "required": ["query"]
                            }
                        },
                        {
                            "name": "apply_edit",
                            "description": "Apply semantic edits to code",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "file_path": {"type": "string"},
                                    "edits": {"type": "array"}
                                },
                                "required": ["file_path", "edits"]
                            }
                        }
                    ]
                }
                
            elif method == "shutdown":
                await self.shutdown()
                result = {}
                
            else:
                raise ValueError(f"Unknown method: {method}")
                
            if request_id is not None:
                self.write_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                })
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            if request_id is not None:
                self.write_response({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                })
                
    async def run(self):
        """Run the stdio server."""
        await self.initialize()
        
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                    
                try:
                    request = json.loads(line.strip())
                    await self.handle_request(request)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.shutdown()


async def main():
    """Main entry point."""
    server = MCPStdioServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())