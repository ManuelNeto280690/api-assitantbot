"""Rate limiting utilities using Redis."""
import time
from typing import Optional
from redis import Redis
from app.config import settings


class RateLimiter:
    """Redis-based rate limiter with sliding window."""
    
    def __init__(self):
        """Initialize rate limiter with Redis connection."""
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> tuple[bool, int]:
        """
        Check if rate limit is exceeded using sliding window.
        
        Args:
            key: Unique key for rate limiting (e.g., "tenant:123:sms")
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        current_count = self.redis.zcard(key)
        
        if current_count < limit:
            # Add current request
            self.redis.zadd(key, {str(now): now})
            self.redis.expire(key, window_seconds)
            return True, limit - current_count - 1
        
        return False, 0
    
    def get_remaining(self, key: str, limit: int, window_seconds: int = 60) -> int:
        """
        Get remaining requests in current window.
        
        Args:
            key: Unique key for rate limiting
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Number of remaining requests
        """
        now = time.time()
        window_start = now - window_seconds
        
        # Remove old entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests
        current_count = self.redis.zcard(key)
        
        return max(0, limit - current_count)
    
    def reset(self, key: str):
        """
        Reset rate limit for a key.
        
        Args:
            key: Unique key to reset
        """
        self.redis.delete(key)


# Global rate limiter instance
rate_limiter = RateLimiter()
