"""
Local disk cache for expensive operations like PDF text extraction.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional, Callable

from common import logger

log = logger(__name__)


class DiskCache:
    """A simple disk-based cache that stores function results as raw bytes."""

    def __init__(self, cache_dir):
        """
        Initialize the disk cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

    def _key_hash(self, content: bytes) -> str:
        """Generate a cache key from content bytes using SHA256 hash."""
        return hashlib.sha256(content).hexdigest()

    def _cache_path(self, key: str) -> Path:
        """Get the full path for a cache key."""
        return self.cache_dir / f"{key}.bin"

    def get(self, key: bytes, fetch: Callable[[], bytes]) -> bytes:
        """
        Retrieve cached result for given content, or compute and cache it on miss.

        Args:
            key: The content bytes to check cache for
            fetch: Function to call when cache miss occurs, should return bytes

        Returns:
            Cached or newly computed result as bytes
        """
        key_hash = self._key_hash(key)
        cache_path = self._cache_path(key_hash)

        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    result = f.read()
                log.info(f"Cache hit for hash {key_hash[:8]}...")
                return result
            except Exception as e:
                log.warning(f"Failed to load cache for hash {key_hash[:8]}...: {e}")
                # Remove corrupted cache file
                cache_path.unlink(missing_ok=True)

        log.info(f"Cache miss for hash {key_hash[:8]}...")

        # Compute result and cache it
        result = fetch()
        try:
            with open(cache_path, "wb") as f:
                f.write(result)
            log.info(f"Cached result for hash {key_hash[:8]}...")
        except Exception as e:
            log.warning(f"Failed to cache result for hash {key_hash[:8]}...: {e}")
            # Clean up any existing cache file on failure
            cache_path.unlink(missing_ok=True)

        return result

    def clear(self) -> None:
        """Clear all cached files."""
        for cache_file in self.cache_dir.glob("*.bin"):
            cache_file.unlink()
        log.info("Cache cleared")
