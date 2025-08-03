"""LSP Client for communicating with language servers."""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pylsp_jsonrpc import streams

from .config import Config

logger = logging.getLogger(__name__)


class LSPServerProcess:
    """Manages a language server process."""
    
    def __init__(self, language: str, command: List[str]):
        """Initialize LSP server process."""
        self.language = language
        self.command = command
        self.process: Optional[subprocess.Popen] = None
        self.reader: Optional[streams.JsonRpcStreamReader] = None
        self.writer: Optional[streams.JsonRpcStreamWriter] = None
        self._request_id = 0
    
    async def start(self):
        """Start the language server process."""
        try:
            self.process = subprocess.Popen(
                self.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            self.reader = streams.JsonRpcStreamReader(self.process.stdout)
            self.writer = streams.JsonRpcStreamWriter(self.process.stdin)
            
            # Initialize the server
            await self._initialize()
            logger.info(f"Started {self.language} language server")
            
        except Exception as e:
            logger.error(f"Failed to start {self.language} server: {e}")
            raise
    
    async def stop(self):
        """Stop the language server process."""
        if self.process:
            try:
                # Send shutdown request
                await self._request("shutdown", {})
                # Send exit notification
                self._notify("exit", {})
                
                # Wait for process to exit
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None
                self.reader = None
                self.writer = None
    
    async def _initialize(self):
        """Send initialize request to server."""
        params = {
            "processId": os.getpid(),
            "rootUri": f"file://{os.getcwd()}",
            "capabilities": {
                "textDocument": {
                    "definition": {"dynamicRegistration": False},
                    "references": {"dynamicRegistration": False},
                    "documentSymbol": {"dynamicRegistration": False},
                }
            },
        }
        
        result = await self._request("initialize", params)
        self._notify("initialized", {})
        return result
    
    def _get_next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id
    
    async def _request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send request and wait for response."""
        msg_id = self._get_next_id()
        
        self.writer.write({
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
            "params": params,
        })
        
        # Read messages until we get our response
        while True:
            raw_msg = self.reader._read_message()
            if raw_msg is None:
                continue
            # Decode if bytes
            if isinstance(raw_msg, bytes):
                import json
                msg = json.loads(raw_msg.decode('utf-8'))
            else:
                msg = raw_msg
                
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise Exception(f"LSP error: {msg['error']}")
                return msg.get("result")
    
    def _notify(self, method: str, params: Dict[str, Any]):
        """Send notification (no response expected)."""
        self.writer.write({
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        })
    
    async def get_definition(self, file_uri: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get definition location."""
        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": character},
        }
        
        result = await self._request("textDocument/definition", params)
        return result[0] if result else None
    
    async def get_references(self, file_uri: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get all references."""
        params = {
            "textDocument": {"uri": file_uri},
            "position": {"line": line, "character": character},
            "context": {"includeDeclaration": True},
        }
        
        result = await self._request("textDocument/references", params)
        return result or []
    
    async def get_symbols(self, file_uri: str) -> List[Dict[str, Any]]:
        """Get document symbols."""
        params = {
            "textDocument": {"uri": file_uri},
        }
        
        result = await self._request("textDocument/documentSymbol", params)
        return result or []


class LSPClient:
    """Client for Language Server Protocol communication."""
    
    # Language server configurations
    LANGUAGE_SERVERS = {
        "python": ["pylsp"],
        "typescript": ["typescript-language-server", "--stdio"],
        "javascript": ["typescript-language-server", "--stdio"],
        "bash": ["bash-language-server", "start"],
        "go": ["gopls", "serve"],
    }
    
    def __init__(self):
        """Initialize LSP client."""
        self.servers: Dict[str, LSPServerProcess] = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize connections to language servers."""
        logger.info("Initializing LSP connections...")
        
        # Start Python language server by default
        await self._start_server("python")
        
        self.initialized = True
    
    async def shutdown(self):
        """Shutdown all LSP connections."""
        logger.info("Shutting down LSP connections...")
        
        for server in self.servers.values():
            await server.stop()
        
        self.servers.clear()
        self.initialized = False
    
    async def _start_server(self, language: str):
        """Start a language server for the given language."""
        if language not in self.LANGUAGE_SERVERS:
            logger.warning(f"No language server configured for {language}")
            return
        
        if language not in self.servers:
            command = self.LANGUAGE_SERVERS[language]
            server = LSPServerProcess(language, command)
            await server.start()
            self.servers[language] = server
    
    def _get_language_from_file(self, file_path: str) -> str:
        """Determine language from file extension."""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".sh": "bash",
            ".bash": "bash",
            ".go": "go",
        }
        
        return language_map.get(ext, "unknown")
    
    async def get_definition(self, file_path: str, position: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Get definition for symbol at given position."""
        language = self._get_language_from_file(file_path)
        
        # Ensure server is started
        await self._start_server(language)
        
        if language in self.servers:
            file_uri = f"file://{os.path.abspath(file_path)}"
            return await self.servers[language].get_definition(
                file_uri, position["line"], position["character"]
            )
        
        return None
    
    async def get_references(self, file_path: str, position: Dict[str, int]) -> List[Dict[str, Any]]:
        """Get all references for symbol at given position."""
        language = self._get_language_from_file(file_path)
        
        # Ensure server is started
        await self._start_server(language)
        
        if language in self.servers:
            file_uri = f"file://{os.path.abspath(file_path)}"
            return await self.servers[language].get_references(
                file_uri, position["line"], position["character"]
            )
        
        return []
    
    async def get_symbols(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all symbols in a file."""
        language = self._get_language_from_file(file_path)
        
        # Ensure server is started
        await self._start_server(language)
        
        if language in self.servers:
            file_uri = f"file://{os.path.abspath(file_path)}"
            return await self.servers[language].get_symbols(file_uri)
        
        return []