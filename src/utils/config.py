"""Configuration helpers for node startup.

Reads runtime configuration from environment variables. The API is a
small static helper that returns a dictionary consumed by the node
startup logic.
"""

import os
from typing import Dict, List


class Config:
    @staticmethod
    def get_node_config() -> Dict:
        """Load node settings from environment with sensible defaults."""
        return {
            "node_id": os.getenv("NODE_ID", "node1"),
            "host": os.getenv("HOST", "0.0.0.0"),
            "port": int(os.getenv("PORT", "5000")),
            "peers": Config._parse_peers(os.getenv("PEERS", "")),
            "data_dir": os.getenv("DATA_DIR", "data"),
        }

    @staticmethod
    def _parse_peers(peers_str: str) -> List[Dict[str, any]]:
        """Turn a comma-separated peers string into a list of dicts.

        Expected format: "peer1:5001,peer2:5002". If hostnames are
        provided as plain names we set them as the host, which works well
        in containerized deployments where service names resolve.
        """
        if not peers_str:
            return []

        out: List[Dict[str, any]] = []
        for token in peers_str.split(","):
            token = token.strip()
            if not token:
                continue
            if ":" in token:
                node_id, port = token.split(":", 1)
                out.append({"node_id": node_id, "host": node_id, "port": int(port)})
        return out