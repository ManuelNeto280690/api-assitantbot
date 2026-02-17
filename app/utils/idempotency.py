"""Idempotency utilities for webhook processing."""
import hashlib
from typing import Optional
from redis import Redis
from app.config import settings


class IdempotencyService:
    """Service for handling idempotent webhook requests."""
    
    def __init__(self, ttl_seconds: int = 86400):  # 24 hours default
        """
        Initialize idempotency service.
        
        Args:
            ttl_seconds: Time to live for idempotency keys
        """
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds
    
    def generate_key(self, *args) -> str:
        """
        Generate idempotency key from arguments.
        
        Args:
            *args: Values to include in key generation
            
        Returns:
            SHA256 hash as idempotency key
        """
        combined = "|".join(str(arg) for arg in args)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def is_processed(self, key: str) -> bool:
        """
        Check if request with this key was already processed.
        
        Args:
            key: Idempotency key
            
        Returns:
            True if already processed
        """
        return self.redis.exists(f"idempotency:{key}") > 0
    
    def mark_processed(self, key: str, result: Optional[str] = None):
        """
        Mark request as processed.
        
        Args:
            key: Idempotency key
            result: Optional result to store
        """
        redis_key = f"idempotency:{key}"
        self.redis.set(redis_key, result or "processed", ex=self.ttl_seconds)
    
    def get_result(self, key: str) -> Optional[str]:
        """
        Get stored result for processed request.
        
        Args:
            key: Idempotency key
            
        Returns:
            Stored result or None
        """
        return self.redis.get(f"idempotency:{key}")
    
    def process_once(self, key: str, func, *args, **kwargs):
        """
        Process function only once for given key.
        
        Args:
            key: Idempotency key
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result (from cache or fresh execution)
        """
        if self.is_processed(key):
            return self.get_result(key)
        
        result = func(*args, **kwargs)
        self.mark_processed(key, str(result))
        return result


# Global idempotency service instance
idempotency_service = IdempotencyService()
