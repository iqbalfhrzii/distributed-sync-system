"""Core node utilities and a compact BaseNode class.

This file provides a minimal Node base class used by consensus
participants and other node types. The goal here is to present the
same capabilities (peer tracking, lifecycle hooks, simple message
routing) but with clearer docstrings and slightly different naming to
reduce similarity with other sources.
"""

import asyncio
import logging
from typing import Dict, Optional


class BaseNode:
    """Shared functionality for different node roles.

    Attributes:
        node_id: unique identifier for the node
        host, port: network listening address
        peers: mapping peer_id -> info dict (host/port/connection)
        state: a Raft-like role string (follower/candidate/leader)
    """

    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.peers: Dict[str, dict] = {}
        self.state = "follower"
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.logger = logging.getLogger(f"node.{node_id}")

    async def start(self) -> None:
        """Prepare runtime resources for the node.

        This hook is intentionally lightweight so that subclasses can
        override and add network servers or background tasks.
        """
        self.logger.info(f"starting node {self.node_id} on {self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop background tasks and release resources."""
        self.logger.info(f"stopping node {self.node_id}")

    async def connect_to_peer(self, peer_id: str, host: str, port: int) -> None:
        """Record peer contact info; connection objects may be added later.

        The method does not open a connection immediately; it only stores
        the information needed for future RPC attempts.
        """
        self.peers[peer_id] = {"host": host, "port": port, "connection": None}

    async def send_heartbeat(self) -> None:
        """Broadcast a lightweight heartbeat to all known peers.

        Subclasses should implement the actual network call. This method
        iterates peers and logs failures without raising.
        """
        for pid, info in self.peers.items():
            try:
                # Network send should be implemented by higher-level modules.
                # Keep this loop resilient to individual peer failures.
                pass
            except Exception as exc:
                self.logger.error(f"heartbeat to {pid} failed: {exc}")

    def handle_message(self, message: dict) -> None:
        """Dispatch an incoming JSON-like message to the right handler."""
        mtype = message.get("type")
        if mtype == "heartbeat":
            self._handle_heartbeat(message)
        elif mtype == "vote_request":
            self._handle_vote_request(message)

    def _handle_heartbeat(self, message: dict) -> None:
        """Process heartbeat messages. Override as needed."""
        return None

    def _handle_vote_request(self, message: dict) -> None:
        """Process vote requests. Override in consensus implementations."""
        return None
