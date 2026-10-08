import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding-window limiter: at most `max_events` per `window` seconds per key."""

    def __init__(self, max_events: int, window: float):
        self.max_events, self.window = max_events, window
        self._hits = defaultdict(deque)

    def allow(self, key) -> bool:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_events:
            return False
        q.append(now)
        if len(self._hits) > 5000:
            self._prune(now)
        return True

    def _prune(self, now: float) -> None:
        for k in [k for k, q in self._hits.items() if not q or now - q[-1] > self.window]:
            del self._hits[k]
