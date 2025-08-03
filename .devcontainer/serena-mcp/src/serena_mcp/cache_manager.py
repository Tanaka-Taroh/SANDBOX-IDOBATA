"""Cache Manager for storing context results."""

import json
import logging
import time
from typing import Any, Dict, Optional

from cachetools import TTLCache

from .config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of context results."""
    
    def __init__(self):
        """Initialize cache manager."""
        # Convert MB to bytes for cache size
        cache_size_bytes = Config.CACHE_SIZE_MB * 1024 * 1024
        
        # Convert days to seconds for TTL
        ttl_seconds = Config.CACHE_TTL_DAYS * 24 * 60 * 60
        
        # Initialize TTL cache
        self.cache = TTLCache(
            maxsize=cache_size_bytes,
            ttl=ttl_seconds,
            getsizeof=self._get_size,
        )
        
        logger.info(
            f"Cache initialized with size: {Config.CACHE_SIZE_MB}MB, "
            f"TTL: {Config.CACHE_TTL_DAYS} days"
        )
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        try:
            value = self.cache.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """Set value in cache."""
        try:
            serialized = json.dumps(value)
            self.cache[key] = serialized
            logger.debug(f"Cached value for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "hits": getattr(self.cache, "hits", 0),
            "misses": getattr(self.cache, "misses", 0),
        }
    
    @staticmethod
    def _get_size(value: str) -> int:
        """Get size of cached value in bytes."""
        return len(value.encode("utf-8"))