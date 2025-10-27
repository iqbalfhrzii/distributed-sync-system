"""src.communication.failure_detector
Reworked simple failure detector used by nodes to monitor peers.

This module provides a lightweight heartbeat-based detector that
records the latest heartbeat timestamp per peer and exposes a small
API to mark heartbeats and check suspected failures. The implementation
is intentionally simple (polling + timeout) to be easy to read and
modify while preserving the original behavior of detecting dead peers.

Notes:
- The detector is non-blocking and intended to be used from asyncio
  tasks in the node process.
- Timeouts are configurable per-peer; in tests you can reduce the
  interval to speed up detection.
"""

import asyncio
import time
from typing import Dict, Optional


class FailureDetector:
	"""Track peer heartbeats and decide if a peer is alive.

	Public methods:
	- mark_heartbeat(peer_id): record that we heard from peer now
	- is_suspected(peer_id): True if last heartbeat is older than timeout
	- start_monitor(interval): optional background task to periodically
	  evaluate peers and call a user callback (if provided)
	"""

	def __init__(self, default_timeout: float = 0.5):
		# default_timeout in seconds (e.g., 0.5s)
		self.default_timeout = default_timeout
		self._last_seen: Dict[str, float] = {}
		self._timeouts: Dict[str, float] = {}
		self._monitor_task: Optional[asyncio.Task] = None
		self._on_suspect = None

	def mark_heartbeat(self, peer_id: str) -> None:
		"""Record a heartbeat arrival from peer_id."""
		self._last_seen[peer_id] = time.time()

	def set_timeout(self, peer_id: str, timeout: float) -> None:
		"""Set a custom timeout for a given peer."""
		self._timeouts[peer_id] = timeout

	def _timeout_for(self, peer_id: str) -> float:
		return self._timeouts.get(peer_id, self.default_timeout)

	def is_suspected(self, peer_id: str) -> bool:
		"""Return True when peer has not been heard from within timeout."""
		last = self._last_seen.get(peer_id)
		if last is None:
			# Never heard from this peer, considered suspect until proven otherwise
			return True
		return (time.time() - last) > self._timeout_for(peer_id)

	def register_suspect_callback(self, cb):
		"""Optional callback(cb: peer_id:str) called for newly suspected peers."""
		self._on_suspect = cb

	async def start_monitor(self, poll_interval: float = 0.1):
		"""Start a background task that checks peers every poll_interval."""
		if self._monitor_task and not self._monitor_task.done():
			return

		async def _run():
			while True:
				for peer in list(self._last_seen.keys()):
					if self.is_suspected(peer) and self._on_suspect:
						try:
							self._on_suspect(peer)
						except Exception:
							# keep the monitor resilient
							pass
				await asyncio.sleep(poll_interval)

		self._monitor_task = asyncio.create_task(_run())

	async def stop_monitor(self):
		if self._monitor_task:
			self._monitor_task.cancel()
			try:
				await self._monitor_task
			except asyncio.CancelledError:
				pass
