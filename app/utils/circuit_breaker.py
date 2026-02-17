"""Circuit breaker pattern for external API calls."""
import time
from enum import Enum
from typing import Callable, Any
from functools import wraps
from redis import Redis
from app.config import settings


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for external API calls.
    
    Prevents cascading failures by stopping requests to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    
    def _get_state_key(self, name: str) -> str:
        """Get Redis key for circuit state."""
        return f"circuit_breaker:{name}:state"
    
    def _get_failure_key(self, name: str) -> str:
        """Get Redis key for failure count."""
        return f"circuit_breaker:{name}:failures"
    
    def _get_last_failure_key(self, name: str) -> str:
        """Get Redis key for last failure time."""
        return f"circuit_breaker:{name}:last_failure"
    
    def get_state(self, name: str) -> CircuitState:
        """Get current circuit state."""
        state = self.redis.get(self._get_state_key(name))
        if not state:
            return CircuitState.CLOSED
        
        # Check if we should transition from OPEN to HALF_OPEN
        if state == CircuitState.OPEN:
            last_failure = self.redis.get(self._get_last_failure_key(name))
            if last_failure:
                time_since_failure = time.time() - float(last_failure)
                if time_since_failure >= self.recovery_timeout:
                    self._set_state(name, CircuitState.HALF_OPEN)
                    return CircuitState.HALF_OPEN
        
        return CircuitState(state)
    
    def _set_state(self, name: str, state: CircuitState):
        """Set circuit state."""
        self.redis.set(self._get_state_key(name), state.value)
    
    def _increment_failures(self, name: str) -> int:
        """Increment failure count and return new count."""
        key = self._get_failure_key(name)
        count = self.redis.incr(key)
        self.redis.expire(key, self.recovery_timeout)
        return count
    
    def _reset_failures(self, name: str):
        """Reset failure count."""
        self.redis.delete(self._get_failure_key(name))
    
    def record_success(self, name: str):
        """Record successful call."""
        self._set_state(name, CircuitState.CLOSED)
        self._reset_failures(name)
    
    def record_failure(self, name: str):
        """Record failed call."""
        failures = self._increment_failures(name)
        self.redis.set(self._get_last_failure_key(name), str(time.time()))
        
        if failures >= self.failure_threshold:
            self._set_state(name, CircuitState.OPEN)
    
    def call(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            name: Circuit breaker name
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        state = self.get_state(name)
        
        if state == CircuitState.OPEN:
            raise Exception(f"Circuit breaker '{name}' is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.record_success(name)
            return result
        except self.expected_exception as e:
            self.record_failure(name)
            raise e


def circuit_breaker(name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
    """
    Decorator for circuit breaker pattern.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        recovery_timeout: Seconds before attempting recovery
    """
    cb = CircuitBreaker(failure_threshold, recovery_timeout)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(name, func, *args, **kwargs)
        return wrapper
    
    return decorator


# Global circuit breaker instance
circuit_breaker_service = CircuitBreaker()
