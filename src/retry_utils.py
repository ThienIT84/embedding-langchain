"""Utilities cho retry logic với exponential backoff."""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, TypeVar, ParamSpec

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator retry với exponential backoff.
    
    Args:
        max_retries: Số lần retry tối đa (mặc định 3)
        initial_delay: Delay ban đầu tính bằng giây (mặc định 1.0s)
        backoff_factor: Hệ số nhân cho mỗi lần retry (mặc định 2.0)
        exceptions: Tuple các exception cần retry (mặc định tất cả Exception)
    
    Example:
        @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
        def call_api():
            return requests.get("https://api.example.com")
        
        # Nếu fail:
        # - Lần 1: retry sau 1s
        # - Lần 2: retry sau 2s
        # - Lần 3: retry sau 4s
        # - Sau đó raise exception
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern để tránh gọi service bị lỗi liên tục.
    
    States:
    - CLOSED: Hoạt động bình thường
    - OPEN: Ngừng gọi service (fast fail)
    - HALF_OPEN: Thử gọi lại sau timeout
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Args:
            failure_threshold: Số lần fail trước khi open circuit
            timeout: Thời gian chờ trước khi thử lại (giây)
            expected_exception: Exception type cần track
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Execute function với circuit breaker logic."""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time < self.timeout:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
            else:
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker HALF_OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Reset khi thành công."""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker CLOSED")
    
    def _on_failure(self):
        """Tăng failure count khi thất bại."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"Circuit breaker OPEN after {self.failure_count} failures")
