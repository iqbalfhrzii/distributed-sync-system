"""Cache node with a simple MESI-like coherence sketch and LRU storage.

The implementation is kept concise: an in-memory LRU for cache lines,
per-node directory bookkeeping and async stubs for fetching,
invalidating and write-back. The goal is readability and testability
rather than a complete coherence protocol.
"""

from enum import Enum
from typing import Dict, Optional, Any
from collections import OrderedDict
import time


class CacheState(Enum):
    MODIFIED = "M"
    EXCLUSIVE = "E"
    SHARED = "S"
    INVALID = "I"


class CacheLine:
    def __init__(self, address: str, data: Any):
        self.address = address
        self.data = data
        self.state = CacheState.INVALID
        self.last_access = time.time()


class LRUCache:
    """Simple LRU container for CacheLine objects."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self._store: OrderedDict[str, CacheLine] = OrderedDict()

    def get(self, address: str) -> Optional[CacheLine]:
        if address in self._store:
            line = self._store.pop(address)
            self._store[address] = line
            line.last_access = time.time()
            return line
        return None

    def put(self, address: str, line: CacheLine) -> None:
        if address in self._store:
            self._store.pop(address)
        elif len(self._store) >= self.capacity:
            self._store.popitem(last=False)
        self._store[address] = line
        line.last_access = time.time()


class CacheNode:
    """Node-local cache with directory bookkeeping for simple coherence."""

    def __init__(self, node_id: str, capacity: int = 1000):
        self.node_id = node_id
        self.cache = LRUCache(capacity)
        # directory: address -> {node_id: CacheState}
        self.directory: Dict[str, Dict[str, CacheState]] = {}
        self.metrics = {"hits": 0, "misses": 0, "invalidations": 0}

    async def read(self, address: str) -> Optional[Any]:
        """Try to read from the local cache; on miss fetch from memory/peers."""
        line = self.cache.get(address)
        if line and line.state != CacheState.INVALID:
            self.metrics["hits"] += 1
            return line.data

        self.metrics["misses"] += 1
        data = await self._fetch_data(address)
        if data is not None:
            new_line = CacheLine(address, data)
            new_line.state = CacheState.EXCLUSIVE if address not in self.directory else CacheState.SHARED
            self.cache.put(address, new_line)
            self._update_directory(address, new_line.state)
        return data

    async def write(self, address: str, data: Any) -> bool:
        """Write to the cache, invalidating other copies when necessary."""
        line = self.cache.get(address)
        if line and line.state in (CacheState.MODIFIED, CacheState.EXCLUSIVE):
            line.data = data
            line.state = CacheState.MODIFIED
            return True

        # Invalidate peer copies then install locally as MODIFIED
        await self._invalidate_other_copies(address)
        new_line = CacheLine(address, data)
        new_line.state = CacheState.MODIFIED
        self.cache.put(address, new_line)
        self._update_directory(address, new_line.state)
        return True

    async def invalidate(self, address: str) -> None:
        line = self.cache.get(address)
        if line:
            if line.state == CacheState.MODIFIED:
                await self._write_back(address, line.data)
            line.state = CacheState.INVALID
            self.metrics["invalidations"] += 1

    def _update_directory(self, address: str, state: CacheState) -> None:
        if address not in self.directory:
            self.directory[address] = {}
        self.directory[address][self.node_id] = state

    async def _fetch_data(self, address: str) -> Optional[Any]:
        """Placeholder: integrate with memory or peer cache queries."""
        return None

    async def _invalidate_other_copies(self, address: str) -> None:
        if address in self.directory:
            for nid in list(self.directory[address].keys()):
                if nid != self.node_id:
                    # send invalidation to nid (networking left to integration)
                    pass

    async def _write_back(self, address: str, data: Any) -> None:
        """Placeholder for writing back modified data to durable store."""
        return None
