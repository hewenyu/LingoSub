import time
import logging
from redis import Redis

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    A simple fixed-window rate limiter using Redis.
    """
    def __init__(self, redis_client: Redis, key: str, limit: int, period: int):
        """
        :param redis_client: An instance of a Redis client.
        :param key: The base key to use for storing rate limit data in Redis.
        :param limit: The number of allowed requests per period.
        :param period: The time period in seconds.
        """
        self.redis = redis_client
        self.key = key
        self.limit = limit
        self.period = period

    def acquire(self):
        """
        Acquires a permit from the rate limiter. Blocks until a permit is available.
        """
        while True:
            current_window = int(time.time() // self.period)
            redis_key = f"{self.key}:{current_window}"
            
            p = self.redis.pipeline()
            p.incr(redis_key)
            p.expire(redis_key, self.period)
            count, _ = p.execute()

            if count <= self.limit:
                logger.debug(f"Rate limit permit acquired. Count: {count}/{self.limit}")
                return True
            else:
                # Calculate how long to wait before the next window starts.
                wait_time = self.period - (time.time() % self.period)
                logger.warning(
                    f"Rate limit exceeded ({self.limit}/{self.period}s). "
                    f"Waiting for {wait_time:.2f}s for the next window."
                )
                time.sleep(wait_time) 