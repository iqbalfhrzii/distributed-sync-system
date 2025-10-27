"""Lightweight PBFT-style agreement helpers (simplified).

This module contains a compact, easy-to-read skeleton of a PBFT-like
protocol. It is intentionally simplified for educational/test use. The
implementation focuses on message flow semantics (pre-prepare,
prepare, commit) while leaving RPC and persistence to the caller.
"""

import asyncio
import logging
from typing import Dict, List, Optional


class PBFTNode:
	"""Minimal PBFT participant used for replicated request ordering.

	The class exposes methods to propose a request and to handle the
	classical PBFT phases. Networking (send/receive) should be wired by
	the application using this object (e.g. via MessageHandler).
	"""

	def __init__(self, node_id: str, peers: List[str]):
		self.node_id = node_id
		self.peers = peers
		self.logger = logging.getLogger(f"pbft.{node_id}")
		self.view = 0
		self.sequence = 0
		self.prepared: Dict[int, List[str]] = {}
		self.committed: Dict[int, List[str]] = {}

	async def propose(self, request: dict) -> int:
		"""Propose a new client request. Returns the assigned sequence number.

		The method increments the local sequence and would normally broadcast
		a pre-prepare message to peers.
		"""
		self.sequence += 1
		seq = self.sequence
		# In a full system you'd broadcast pre-prepare here
		self.logger.debug("propose seq=%d request=%s", seq, request)
		return seq

	def handle_pre_prepare(self, seq: int, request: dict) -> None:
		"""Called when a pre-prepare arrives from the primary."""
		# Record and advance to prepare phase
		self.logger.debug("pre-prepare seq=%d", seq)

	def handle_prepare(self, seq: int, sender: str) -> None:
		"""Handle a prepare message from a peer."""
		self.prepared.setdefault(seq, []).append(sender)
		# In a real PBFT, check for 2f+1 prepares before committing

	def handle_commit(self, seq: int, sender: str) -> None:
		"""Handle a commit message; when enough commits are seen the request is executed."""
		self.committed.setdefault(seq, []).append(sender)

	def is_committed(self, seq: int) -> bool:
		"""Return True when a sequence number has reached a commit quorum."""
		# Quorum logic is context-dependent; keep it pluggable.
		commits = len(self.committed.get(seq, []))
		return commits > (len(self.peers) * 2 / 3)
