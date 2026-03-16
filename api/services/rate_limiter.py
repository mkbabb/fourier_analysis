"""In-memory sliding-window rate limiter keyed by hashed IP with LRU eviction."""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request

# ---------------------------------------------------------------------------
# IP hashing helper
# ---------------------------------------------------------------------------

MAX_ENTRIES = 50_000


def hash_ip(ip: str) -> str:
    """Return the SHA-256 hex digest of a raw IP string."""
    return hashlib.sha256(ip.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Sliding-window rate limiter
# ---------------------------------------------------------------------------


@dataclass
class _BucketEntry:
    """Timestamps of requests inside the current window."""

    timestamps: list[float] = field(default_factory=list)


class SlidingWindowLimiter:
    """Sliding-window rate limiter with LRU eviction.

    Parameters
    ----------
    max_requests:
        Maximum number of requests allowed inside *window_seconds*.
    window_seconds:
        Length of the sliding window in seconds.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # OrderedDict gives us O(1) move-to-end (LRU refresh) and popitem(last=False)
        self._buckets: OrderedDict[str, _BucketEntry] = OrderedDict()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _evict_expired(self, now: float) -> None:
        """Remove the oldest expired entries until we are under *MAX_ENTRIES*."""
        while len(self._buckets) > MAX_ENTRIES:
            # Pop the least-recently-used key
            key, entry = self._buckets.popitem(last=False)
            # Keep only timestamps still inside the window
            cutoff = now - self.window_seconds
            alive = [t for t in entry.timestamps if t > cutoff]
            if alive:
                # Still active — put it back at the *end* (most-recent)
                entry.timestamps = alive
                self._buckets[key] = entry
            # If no alive timestamps, the entry stays evicted (dropped)

    def _prune_bucket(self, entry: _BucketEntry, now: float) -> None:
        cutoff = now - self.window_seconds
        entry.timestamps = [t for t in entry.timestamps if t > cutoff]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check(self, hashed_key: str) -> None:
        """Record a hit and raise *HTTPException(429)* if over limit."""
        now = time.monotonic()

        # Evict if we are at capacity
        if len(self._buckets) >= MAX_ENTRIES:
            self._evict_expired(now)

        entry = self._buckets.get(hashed_key)
        if entry is None:
            entry = _BucketEntry()
            self._buckets[hashed_key] = entry
        else:
            # Move to end (mark as recently used)
            self._buckets.move_to_end(hashed_key)

        self._prune_bucket(entry, now)

        if len(entry.timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
            )

        entry.timestamps.append(now)


# ---------------------------------------------------------------------------
# Pre-configured limiter instances
# ---------------------------------------------------------------------------

login_limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60)
like_limiter = SlidingWindowLimiter(max_requests=10, window_seconds=60)
write_limiter = SlidingWindowLimiter(max_requests=10, window_seconds=60)
admin_limiter = SlidingWindowLimiter(max_requests=30, window_seconds=60)


# ---------------------------------------------------------------------------
# FastAPI dependency factories
# ---------------------------------------------------------------------------


def _make_dependency(limiter: SlidingWindowLimiter):
    """Return an async FastAPI dependency that enforces *limiter*."""

    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        hashed = hash_ip(client_ip)
        limiter.check(hashed)

    return _dependency


require_login_limit = _make_dependency(login_limiter)
require_like_limit = _make_dependency(like_limiter)
require_write_limit = _make_dependency(write_limiter)
require_admin_limit = _make_dependency(admin_limiter)
