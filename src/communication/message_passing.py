"""Lightweight message-passing utilities for node-to-node RPCs.

This module exposes a small asyncio-based server/client helper. The
public interface remains intentionally simple:
- register_handler(message_type, callback)
- send_message(host, port, message) -> dict|None

Internally the class uses newline-delimited JSON over TCP sockets to
exchange messages and responses.
"""

import asyncio
import json
from typing import Callable, Dict, Optional


class MessageHandler:
    """Async TCP JSON messenger for inter-node calls.

    The class keeps a registry of message-type handlers. When a message
    arrives the appropriate handler is invoked and its result is sent
    back as a JSON reply.
    """

    def __init__(self, node_id: str, host: str, port: int):
        self.node_id = node_id
        self.host = host
        self.port = port
        self._handlers: Dict[str, Callable] = {}
        self._server: Optional[asyncio.Server] = None

    async def start(self) -> None:
        """Start listening for peer connections."""
        self._server = await asyncio.start_server(self._handle_connection, self.host, self.port)
        async with self._server:
            await self._server.serve_forever()

    async def stop(self) -> None:
        """Shut down the TCP server gracefully."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    def register_handler(self, message_type: str, callback: Callable) -> None:
        """Register a coroutine callback for a given message type."""
        self._handlers[message_type] = callback

    async def send_message(self, dest_host: str, dest_port: int, message: dict) -> Optional[dict]:
        """Send a JSON message to dest_host:dest_port and await a JSON reply.

        Returns the decoded response dict or None on failure.
        """
        try:
            reader, writer = await asyncio.open_connection(dest_host, dest_port)
            writer.write(json.dumps(message).encode() + b"\n")
            await writer.drain()

            raw = await reader.readline()
            writer.close()
            await writer.wait_closed()
            if not raw:
                return None
            return json.loads(raw.decode())
        except Exception as exc:  # keep broad to avoid raising across network boundaries
            print(f"[MessageHandler] send_message error: {exc}")
            return None

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            raw = await reader.readline()
            if not raw:
                writer.close()
                await writer.wait_closed()
                return

            message = json.loads(raw.decode())
            mtype = message.get("type")

            handler = self._handlers.get(mtype)
            if handler is None:
                reply = {"status": "error", "message": "unknown type"}
            else:
                # Handler may be sync or async; support both
                res = handler(message)
                if asyncio.iscoroutine(res):
                    res = await res
                reply = res if isinstance(res, dict) else {"result": res}

            writer.write(json.dumps(reply).encode() + b"\n")
            await writer.drain()
        except Exception as exc:
            print(f"[MessageHandler] connection handling error: {exc}")
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
