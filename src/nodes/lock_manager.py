"""A compact lock manager for coordinating resource locks within a node.

This implementation is intentionally simple: it provides local lock
semantics (acquire/release) with optional timeouts and owner tracking.
In a distributed deployment the high-level system should make these
operations durable/serialized (for example, behind a consensus
replicated log). The module's API is synchronous-friendly and also
usable from asyncio code.
"""

import asyncio
import time
from typing import Dict, Optional


class LockInfo:
	def __init__(self, owner: str, lock_type: str, expires_at: Optional[float]):
		self.owner = owner
		self.lock_type = lock_type
		self.expires_at = expires_at


class LockManager:
	"""Manage in-process locks keyed by resource name.

	Methods
	- acquire(resource, owner, lock_type, timeout=None) -> bool
	- release(resource, owner) -> bool
	- status(resource) -> Optional[LockInfo]
	"""

	def __init__(self):
		self._locks: Dict[str, LockInfo] = {}
		self._locks_locks: Dict[str, asyncio.Lock] = {}

	def _get_lock(self, resource: str) -> asyncio.Lock:
		if resource not in self._locks_locks:
			self._locks_locks[resource] = asyncio.Lock()
		return self._locks_locks[resource]

	async def acquire(self, resource: str, owner: str, lock_type: str = "exclusive", timeout: Optional[float] = None) -> bool:
		"""Attempt to acquire a lock for `resource` on behalf of `owner`.

		If timeout is provided this call will wait up to `timeout` seconds
		for the lock to become available. Returns True when acquired.
		"""
		lock = self._get_lock(resource)
		acquired = False
		try:
			if timeout is None:
				await lock.acquire()
				acquired = True
			else:
				acquired = await asyncio.wait_for(lock.acquire(), timeout=timeout)
		except asyncio.TimeoutError:
			return False

		if not acquired:
			return False

		try:
			# Check existing lock info and expire if needed
			cur = self._locks.get(resource)
			if cur and cur.expires_at and cur.expires_at < time.time():
				# expired — remove it
				del self._locks[resource]

			if resource in self._locks:
				# someone else holds the logical lock
				return False

			expires_at = None
			if timeout is not None:
				expires_at = time.time() + timeout

			self._locks[resource] = LockInfo(owner=owner, lock_type=lock_type, expires_at=expires_at)
			return True
		finally:
			# always release the internal asyncio lock so others can attempt
			try:
				lock.release()
			except Exception:
				pass

	async def release(self, resource: str, owner: str) -> bool:
		"""Release a lock previously acquired by `owner`. Returns True if released."""
		lock = self._get_lock(resource)
		async with lock:
			info = self._locks.get(resource)
			if not info:
				return False
			if info.owner != owner:
				return False
			del self._locks[resource]
			return True

	def status(self, resource: str) -> Optional[LockInfo]:
		"""Return LockInfo for a resource or None if unlocked."""
		info = self._locks.get(resource)
		if info and info.expires_at and info.expires_at < time.time():
			# expired — treat as unlocked
			del self._locks[resource]
			return None
		return info

	def list_locks(self) -> Dict[str, Dict[str, Optional[float]]]:
		"""Return a snapshot of current locks: resource -> {owner, type, expires_at}.

		Expired locks are omitted from the snapshot and cleaned up.
		"""
		out: Dict[str, Dict[str, Optional[float]]] = {}
		for res in list(self._locks.keys()):
			info = self._locks.get(res)
			if not info:
				continue
			if info.expires_at and info.expires_at < time.time():
				# cleanup expired
				del self._locks[res]
				continue
			out[res] = {"owner": info.owner, "type": info.lock_type, "expires_at": info.expires_at}
		return out
