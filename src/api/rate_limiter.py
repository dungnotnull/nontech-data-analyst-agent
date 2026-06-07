import time
import threading
from collections import defaultdict
from functools import wraps


class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            bucket = self._buckets[key]
            bucket = [t for t in bucket if now - t < self.window_seconds]
            self._buckets[key] = bucket
            if len(bucket) >= self.max_requests:
                return False
            bucket.append(now)
            return True

    def remaining(self, key: str) -> int:
        now = time.time()
        with self._lock:
            bucket = self._buckets.get(key, [])
            bucket = [t for t in bucket if now - t < self.window_seconds]
            self._buckets[key] = bucket
            return max(0, self.max_requests - len(bucket))

    def reset(self, key: str):
        with self._lock:
            self._buckets.pop(key, None)


upload_limiter = RateLimiter(max_requests=10, window_seconds=3600)
analyze_limiter = RateLimiter(max_requests=100, window_seconds=3600)
