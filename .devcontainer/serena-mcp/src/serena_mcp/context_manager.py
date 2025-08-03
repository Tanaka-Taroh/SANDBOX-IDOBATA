"""Context Manager for aggregating and optimizing code context."""

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import tiktoken

from .cache_manager import CacheManager
from .config import Config
from .lsp_client import LSPClient

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context extraction and optimization."""
    
    def __init__(self, lsp_client: LSPClient):
        """Initialize context manager."""
        self.lsp_client = lsp_client
        self.cache = CacheManager()
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        self.workspace_root = os.getcwd()
    
    async def get_context(
        self,
        query: str,
        scope: str = "function",
        max_tokens: int = Config.MAX_TOKENS
    ) -> Dict[str, Any]:
        """Get optimized context for the given query."""
        # Generate cache key
        cache_key = self._generate_cache_key(query, scope, max_tokens)
        
        # Check cache
        cached_result = self.cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {query}")
            return cached_result
        
        # Extract context based on scope
        logger.info(f"Extracting context for query: {query} with scope: {scope}")
        
        # Parse the query to identify file and symbol
        file_path, symbol_name = self._parse_query(query)
        
        if not file_path:
            # Search for symbol across workspace
            file_path = await self._find_symbol_file(symbol_name)
        
        if not file_path:
            logger.warning(f"Could not find file for query: {query}")
            return self._empty_result()
        
        # Extract symbols based on scope
        symbols = await self._extract_symbols(file_path, symbol_name, scope)
        dependencies = await self._extract_dependencies(symbols)
        references = await self._extract_references(symbols)
        
        # Calculate token savings
        raw_tokens = await self._estimate_raw_tokens(file_path, scope)
        optimized_tokens = self._count_tokens(symbols, dependencies, references)
        tokens_saved = max(0, raw_tokens - optimized_tokens)
        
        result = {
            "symbols": symbols,
            "dependencies": dependencies,
            "references": references,
            "tokens_saved": tokens_saved,
        }
        
        # Cache result
        self.cache.set(cache_key, result)
        
        return result
    
    def _generate_cache_key(self, query: str, scope: str, max_tokens: int) -> str:
        """Generate cache key for the request."""
        key_data = f"{query}:{scope}:{max_tokens}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _parse_query(self, query: str) -> Tuple[Optional[str], str]:
        """Parse query to extract file path and symbol name.
        
        Examples:
        - "UserService.authenticate" -> (None, "authenticate")
        - "/src/user.py:UserService" -> ("/src/user.py", "UserService")
        - "user.py:authenticate" -> ("user.py", "authenticate")
        """
        # Check for explicit file:symbol pattern
        if ":" in query:
            file_part, symbol_part = query.split(":", 1)
            if os.path.exists(file_part):
                return file_part, symbol_part
            # Try to find file in workspace
            found_file = self._find_file_in_workspace(file_part)
            if found_file:
                return found_file, symbol_part
            # Return None for file_path if not found, but keep the symbol
            return None, symbol_part
        
        # Check for class.method pattern
        if "." in query:
            parts = query.split(".")
            if len(parts) == 2:
                return None, parts[1]  # Return method name
        
        # Just a symbol name
        return None, query
    
    def _find_file_in_workspace(self, file_name: str) -> Optional[str]:
        """Find file in workspace by name."""
        for root, dirs, files in os.walk(self.workspace_root):
            if file_name in files:
                return os.path.join(root, file_name)
        return None
    
    async def _find_symbol_file(self, symbol_name: str) -> Optional[str]:
        """Find file containing the given symbol."""
        # Search Python files for now
        # TODO: Extend to other languages
        for root, dirs, files in os.walk(self.workspace_root):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Simple pattern matching for class/function definitions
                            if re.search(rf'^\s*(class|def)\s+{symbol_name}\b', content, re.MULTILINE):
                                return file_path
                    except Exception:
                        continue
        return None
    
    async def _extract_symbols(self, file_path: str, symbol_name: str, scope: str) -> List[Dict[str, Any]]:
        """Extract relevant symbols based on file, symbol name and scope."""
        symbols = []
        
        # Get all symbols in the file
        file_symbols = await self.lsp_client.get_symbols(file_path)
        
        # Filter based on symbol name and scope
        for symbol in file_symbols:
            if scope == "function" and symbol_name in symbol.get("name", ""):
                symbols.append(self._format_symbol(symbol, file_path))
            elif scope == "class":
                # Include whole class if symbol is part of it
                if symbol.get("kind") == 5 or symbol_name in symbol.get("name", ""):  # Class kind
                    symbols.append(self._format_symbol(symbol, file_path))
            elif scope == "file":
                # Include all symbols in file
                symbols.append(self._format_symbol(symbol, file_path))
        
        # If no symbols found via LSP, fallback to basic extraction
        if not symbols and os.path.exists(file_path):
            symbols.append({
                "name": symbol_name,
                "kind": "Unknown",
                "location": {
                    "file": file_path,
                    "line": 1,
                },
                "documentation": f"Symbol {symbol_name} in {os.path.basename(file_path)}",
            })
        
        return symbols
    
    def _format_symbol(self, lsp_symbol: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """Format LSP symbol into our format."""
        location = lsp_symbol.get("location") or lsp_symbol.get("range", {})
        start = location.get("start", {"line": 0})
        
        return {
            "name": lsp_symbol.get("name", "Unknown"),
            "kind": self._get_symbol_kind_name(lsp_symbol.get("kind", 0)),
            "location": {
                "file": file_path,
                "line": start.get("line", 0),
            },
            "documentation": lsp_symbol.get("detail", ""),
        }
    
    def _get_symbol_kind_name(self, kind: int) -> str:
        """Convert LSP SymbolKind number to name."""
        kind_map = {
            1: "File", 2: "Module", 3: "Namespace", 4: "Package",
            5: "Class", 6: "Method", 7: "Property", 8: "Field",
            9: "Constructor", 10: "Enum", 11: "Interface", 12: "Function",
            13: "Variable", 14: "Constant", 15: "String", 16: "Number",
            17: "Boolean", 18: "Array", 19: "Object", 20: "Key",
            21: "Null", 22: "EnumMember", 23: "Struct", 24: "Event",
            25: "Operator", 26: "TypeParameter"
        }
        return kind_map.get(kind, "Unknown")
    
    async def _extract_dependencies(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract dependencies for the given symbols."""
        dependencies = []
        seen_modules = set()
        
        for symbol in symbols:
            file_path = symbol["location"]["file"]
            if not os.path.exists(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract import statements (Python example)
                import_pattern = r'^\s*(?:from\s+(\S+)\s+)?import\s+(.+)$'
                for match in re.finditer(import_pattern, content, re.MULTILINE):
                    module = match.group(1) or match.group(2).split()[0]
                    if module and module not in seen_modules:
                        seen_modules.add(module)
                        dependencies.append({
                            "module": module,
                            "summary": f"Imported by {os.path.basename(file_path)}",
                        })
            except Exception:
                continue
        
        return dependencies
    
    async def _extract_references(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract references for the given symbols."""
        references = []
        
        for symbol in symbols:
            file_path = symbol["location"]["file"]
            line = symbol["location"]["line"]
            
            # Get references via LSP
            refs = await self.lsp_client.get_references(
                file_path,
                {"line": line, "character": 0}
            )
            
            for ref in refs[:5]:  # Limit to 5 references
                ref_file = ref.get("uri", "").replace("file://", "")
                ref_line = ref.get("range", {}).get("start", {}).get("line", 0)
                
                if ref_file and ref_file != file_path:
                    references.append({
                        "file": ref_file,
                        "line": ref_line,
                        "context": f"Reference to {symbol['name']}",
                    })
        
        return references
    
    async def _estimate_raw_tokens(self, file_path: str, scope: str) -> int:
        """Estimate tokens for raw file inclusion."""
        if not os.path.exists(file_path):
            return 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if scope == "function":
                # Estimate ~500 tokens per function
                return 500
            elif scope == "class":
                # Estimate ~2000 tokens per class
                return 2000
            else:  # file
                # Count actual tokens
                return len(self.encoder.encode(content))
        except Exception:
            return 1000  # Default estimate
    
    def _count_tokens(
        self,
        symbols: List[Dict[str, Any]],
        dependencies: List[Dict[str, str]],
        references: List[Dict[str, Any]]
    ) -> int:
        """Count tokens in the optimized context."""
        # Convert to string representation
        context_str = str({
            "symbols": symbols,
            "dependencies": dependencies,
            "references": references,
        })
        
        return len(self.encoder.encode(context_str))
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no context found."""
        return {
            "symbols": [],
            "dependencies": [],
            "references": [],
            "tokens_saved": 0,
        }
    
    async def find_symbol(self, symbol_name: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Find symbol definitions across the codebase."""
        logger.info(f"Finding symbol: {symbol_name}, language: {language}")
        
        # Find file containing the symbol
        file_path = await self._find_symbol_file(symbol_name)
        
        if not file_path:
            return {
                "symbol_name": symbol_name,
                "found": False,
                "message": f"Symbol '{symbol_name}' not found in codebase",
                "locations": []
            }
        
        # Get symbol details
        symbols = await self._extract_symbols(file_path, symbol_name, "function")
        
        locations = []
        for symbol in symbols:
            locations.append({
                "file": symbol["location"]["file"],
                "line": symbol["location"]["line"],
                "kind": symbol["kind"],
                "name": symbol["name"],
                "documentation": symbol.get("documentation", "")
            })
        
        return {
            "symbol_name": symbol_name,
            "found": True,
            "message": f"Found {len(locations)} occurrence(s) of '{symbol_name}'",
            "locations": locations
        }
    
    async def apply_edit(self, file_path: str, edits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply semantic edits to code."""
        logger.info(f"Applying edits to: {file_path}")
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"File not found: {file_path}",
                "edits_applied": 0
            }
        
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            edits_applied = 0
            
            # Sort edits by line number in reverse order to avoid offset issues
            sorted_edits = sorted(edits, key=lambda x: x.get('line', 0), reverse=True)
            
            for edit in sorted_edits:
                edit_type = edit.get('type', 'replace')
                line_num = edit.get('line', 0)
                new_text = edit.get('text', '')
                
                if edit_type == 'replace' and 0 <= line_num < len(lines):
                    lines[line_num] = new_text
                    edits_applied += 1
                elif edit_type == 'insert':
                    if 0 <= line_num <= len(lines):
                        lines.insert(line_num, new_text)
                        edits_applied += 1
                elif edit_type == 'delete':
                    if 0 <= line_num < len(lines):
                        del lines[line_num]
                        edits_applied += 1
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            return {
                "success": True,
                "message": f"Successfully applied {edits_applied} edit(s) to {file_path}",
                "edits_applied": edits_applied
            }
            
        except Exception as e:
            logger.error(f"Error applying edits to {file_path}: {e}")
            return {
                "success": False,
                "message": f"Error applying edits: {str(e)}",
                "edits_applied": 0
            }