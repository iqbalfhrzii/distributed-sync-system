"""Simple metrics collector used by nodes for counters and gauges.

This module provides a tiny in-process metrics sink that other parts
of the system can import and increment. It is not a replacement for
Prometheus, but it is useful for tests and local instrumentation.
"""

from typing import Dict
from threading import Lock


_lock = Lock()
_counters: Dict[str, int] = {}


def inc(metric: str, value: int = 1) -> None:
	"""Increment a counter by value (default 1)."""
	with _lock:
		_counters[metric] = _counters.get(metric, 0) + value


def get(metric: str) -> int:
	"""Read counter value (0 if missing)."""
	with _lock:
		return _counters.get(metric, 0)


def snapshot() -> Dict[str, int]:
	"""Return a shallow copy of all counters."""
	with _lock:
		return dict(_counters)
