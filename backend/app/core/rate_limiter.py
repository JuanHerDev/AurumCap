import asyncio
from collections import deque
from datetime import datetime, timedelta


class RateLimiter:
    """
    Token bucket rate limiter for TwelveData free plan.
    Allows max_calls per window_seconds, queuing excess requests.
    """

    def __init__(self, max_calls: int = 6, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._calls: deque = deque()
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a request slot is available."""
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # Remove calls outside the window
            while self._calls and self._calls[0] < window_start:
                self._calls.popleft()

            if len(self._calls) >= self.max_calls:
                # Calculate wait time until oldest call expires
                oldest = self._calls[0]
                wait_seconds = (
                    oldest + timedelta(seconds=self.window_seconds) - now
                ).total_seconds() + 2.0  # 2s buffer

                print(f"[RateLimiter] Rate limit reached — waiting {wait_seconds:.1f}s")
                await asyncio.sleep(wait_seconds)

                # Clean up again after waiting
                now = datetime.utcnow()
                window_start = now - timedelta(seconds=self.window_seconds)
                while self._calls and self._calls[0] < window_start:
                    self._calls.popleft()

            self._calls.append(datetime.utcnow())


# Global instance — shared across all TwelveData calls
twelvedata_limiter = RateLimiter(max_calls=6, window_seconds=60)