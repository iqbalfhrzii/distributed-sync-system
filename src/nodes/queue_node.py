"""Sharded queue utilities built on a consistent-hashing ring.

The module offers a compact in-memory queue sharding implementation
where each queue name is mapped to an owner node using a hash ring.
Networking and persistence are left as stubs for the integrator to
implement according to their environment.
"""

import hashlib
from typing import Dict, List, Optional
import asyncio


class ConsistentHash:
    """A small consistent-hash helper (virtual nodes / replicas)."""

    def __init__(self, nodes: List[str], replicas: int = 3):
        self.replicas = replicas
        self.ring: Dict[int, str] = {}
        self._sorted_keys: List[int] = []
        for n in nodes:
            self.add_node(n)

    def add_node(self, node: str) -> None:
        for i in range(self.replicas):
            k = self._hash(f"{node}:{i}")
            self.ring[k] = node
        self._sorted_keys = sorted(self.ring.keys())

    def remove_node(self, node: str) -> None:
        for i in range(self.replicas):
            k = self._hash(f"{node}:{i}")
            self.ring.pop(k, None)
        self._sorted_keys = sorted(self.ring.keys())

    def get_node(self, key: str) -> str:
        if not self.ring:
            raise RuntimeError("no nodes in ring")
        h = self._hash(key)
        for rk in self._sorted_keys:
            if h <= rk:
                return self.ring[rk]
        return self.ring[self._sorted_keys[0]]

    @staticmethod
    def _hash(key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)


class DistributedQueue:
    """Sharded queues mapped to nodes via a ConsistentHash ring."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.queues: Dict[str, List[dict]] = {}
        self.hash_ring: Optional[ConsistentHash] = None
        self.persistence_path = f"data/queue_{node_id}"

    async def initialize(self, nodes: List[str]) -> None:
        self.hash_ring = ConsistentHash(nodes)
        await self._load_persistent_data()

    async def enqueue(self, queue_name: str, item: dict) -> bool:
        node = self.hash_ring.get_node(queue_name)
        if node == self.node_id:
            self.queues.setdefault(queue_name, []).append(item)
            await self._persist_queue(queue_name)
            return True
        return await self._forward_enqueue(node, queue_name, item)

    async def dequeue(self, queue_name: str) -> Optional[dict]:
        node = self.hash_ring.get_node(queue_name)
        if node == self.node_id:
            q = self.queues.get(queue_name)
            if not q:
                return None
            item = q.pop(0)
            await self._persist_queue(queue_name)
            return item
        return await self._forward_dequeue(node, queue_name)

    async def _persist_queue(self, queue_name: str) -> None:
        """Persist queue to disk - stub for integrators."""
        return None

    async def _load_persistent_data(self) -> None:
        """Load previously persisted queues - stub."""
        return None

    async def _forward_enqueue(self, node: str, queue_name: str, item: dict) -> bool:
        """Forward request to another node (networking left to caller)."""
        return False

    async def _forward_dequeue(self, node: str, queue_name: str) -> Optional[dict]:
        """Forward dequeue to responsible node."""
        return None
