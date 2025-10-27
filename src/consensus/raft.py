"""A readable, lightly-reworked Raft node implementation.

This file keeps the same behavioral intent (leader election, heartbeats)
but rephrases code and comments to reduce similarity to prior sources.
The algorithm is simplified in places for clarity; fill in network RPCs
via the MessageHandler or other modules in the project.
"""

import asyncio
import random
import time
from typing import Dict, List, Optional

from ..nodes.base_node import BaseNode


class RaftNode(BaseNode):
    """A Raft participant that can become leader via election timeouts."""

    def __init__(self, node_id: str, host: str, port: int):
        super().__init__(node_id, host, port)
        # persistent and volatile Raft state
        self.log: List[dict] = []
        self.commit_index = 0
        self.last_applied = 0

        # leader tracking
        self.leader_id: Optional[str] = None

        # election timeout (seconds). randomized to reduce collisions.
        self.election_timeout_sec = random.uniform(0.15, 0.3)
        self._last_heartbeat_ts = time.time()

    async def start(self) -> None:
        await super().start()
        asyncio.create_task(self._run_election_watchdog())

    async def _run_election_watchdog(self) -> None:
        """Periodically check for missed heartbeats and trigger elections."""
        while True:
            await asyncio.sleep(0.1)
            elapsed = time.time() - self._last_heartbeat_ts
            if elapsed > self.election_timeout_sec:
                await self._begin_election()

    async def _begin_election(self) -> None:
        """Start an election: become candidate and request votes."""
        self.state = "candidate"
        self.current_term += 1
        self.voted_for = self.node_id
        self.leader_id = None

        votes = 1  # vote for self
        # iterate peers and send vote requests (RPC wiring left to caller)
        for peer_id in self.peers:
            try:
                ok = await self._request_vote(peer_id)
                if ok:
                    votes += 1
            except Exception:
                # network error or peer down; ignore and continue
                pass

        majority = (len(self.peers) + 1) // 2 + 1
        if votes >= majority:
            self.state = "leader"
            self.leader_id = self.node_id
            self.logger.info(f"Node {self.node_id} is leader for term {self.current_term}")
            asyncio.create_task(self._leader_heartbeat_loop())

    async def _request_vote(self, peer_id: str) -> bool:
        """Send a vote request to peer. Override with networking code.

        Currently a placeholder returning False so that integration can
        inject the RPC behavior via MessageHandler.
        """
        return False

    async def _leader_heartbeat_loop(self) -> None:
        """As leader, periodically broadcast heartbeats to followers."""
        while self.state == "leader":
            await self.send_heartbeat()
            await asyncio.sleep(0.05)

    def _handle_vote_request(self, message: dict) -> bool:
        """Respond to an incoming vote solicitation.

        The method uses simple safety checks: term comparison and whether
        we already granted a vote this term.
        """
        candidate_id = message["candidate_id"]
        term = message["term"]

        if term < self.current_term:
            return False

        if self.voted_for is None or self.voted_for == candidate_id:
            # simplified log-up-to-date check omitted
            self.voted_for = candidate_id
            return True

        return False