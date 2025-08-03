"""Mock LSP server for testing."""

import asyncio
from typing import Any, Dict, List, Optional


class MockLSPServerProcess:
    """Mock LSP server process for testing."""
    
    def __init__(self, language: str, command: List[str]):
        """Initialize mock LSP server process."""
        self.language = language
        self.command = command
        self.started = False
        self._request_id = 0
    
    async def start(self):
        """Start the mock language server process."""
        await asyncio.sleep(0.01)  # Simulate startup time
        self.started = True
    
    async def stop(self):
        """Stop the mock language server process."""
        await asyncio.sleep(0.01)  # Simulate shutdown time
        self.started = False
    
    async def get_definition(self, file_uri: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """Get mock definition location."""
        return {
            "uri": file_uri,
            "range": {
                "start": {"line": line, "character": 0},
                "end": {"line": line, "character": 80}
            }
        }
    
    async def get_references(self, file_uri: str, line: int, character: int) -> List[Dict[str, Any]]:
        """Get mock references."""
        return [
            {
                "uri": file_uri,
                "range": {
                    "start": {"line": line, "character": 0},
                    "end": {"line": line, "character": 80}
                }
            },
            {
                "uri": file_uri,
                "range": {
                    "start": {"line": line + 10, "character": 5},
                    "end": {"line": line + 10, "character": 25}
                }
            }
        ]
    
    async def get_symbols(self, file_uri: str) -> List[Dict[str, Any]]:
        """Get mock document symbols."""
        return [
            {
                "name": "MockClass",
                "kind": 5,  # Class
                "range": {
                    "start": {"line": 5, "character": 0},
                    "end": {"line": 15, "character": 0}
                },
                "selectionRange": {
                    "start": {"line": 5, "character": 6},
                    "end": {"line": 5, "character": 15}
                }
            },
            {
                "name": "mock_function",
                "kind": 12,  # Function
                "range": {
                    "start": {"line": 20, "character": 0},
                    "end": {"line": 25, "character": 0}
                },
                "selectionRange": {
                    "start": {"line": 20, "character": 4},
                    "end": {"line": 20, "character": 17}
                }
            }
        ]