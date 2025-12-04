"""Tests cho retry utilities."""
import pytest
import time
from src.retry_utils import retry_with_backoff, CircuitBreaker

def test_retry_success_first_attempt():
    """Test function thành công ngay lần đầu."""
    call_count = 0
    
    @retry_with_backoff(max_retries=3)
    def always_succeed():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = always_succeed()
    
    assert result == "success"
    assert call_count == 1  # Chỉ gọi 1 lần

def test_retry_success_after_failures():
    """Test function thành công sau vài lần retry."""
    call_count = 0
    
    @retry_with_backoff(max_retries=3, initial_delay=0.1)
    def succeed_on_third():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "success"
    
    result = succeed_on_third()
    
    assert result == "success"
    assert call_count == 3

def test_retry_max_retries_exceeded():
    """Test raise exception khi vượt max_retries."""
    call_count = 0
    
    @retry_with_backoff(max_retries=2, initial_delay=0.1)
    def always_fail():
        nonlocal call_count
        call_count += 1
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError, match="Always fails"):
        always_fail()
    
    assert call_count == 3  # 1 lần đầu + 2 retries

def test_retry_exponential_backoff():
    """Test exponential backoff timing."""
    times = []
    
    @retry_with_backoff(max_retries=3, initial_delay=0.1, backoff_factor=2.0)
    def track_timing():
        times.append(time.time())
        if len(times) < 4:
            raise ValueError("Retry")
        return "success"
    
    track_timing()
    
    # Kiểm tra delays tăng dần
    assert len(times) == 4
    # Delay 1: ~0.1s, Delay 2: ~0.2s, Delay 3: ~0.4s

def test_retry_specific_exceptions():
    """Test chỉ retry với specific exceptions."""
    call_count = 0
    
    @retry_with_backoff(max_retries=2, initial_delay=0.1, exceptions=(ValueError,))
    def raise_different_errors():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Retry this")
        raise TypeError("Don't retry this")
    
    with pytest.raises(TypeError, match="Don't retry this"):
        raise_different_errors()
    
    assert call_count == 2  # ValueError được retry, TypeError không

def test_circuit_breaker_closed_state():
    """Test circuit breaker ở trạng thái CLOSED."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1.0)
    
    def succeed():
        return "ok"
    
    result = cb.call(succeed)
    assert result == "ok"
    assert cb.state == "CLOSED"

def test_circuit_breaker_opens_after_threshold():
    """Test circuit breaker mở sau khi vượt threshold."""
    cb = CircuitBreaker(failure_threshold=3, timeout=1.0, expected_exception=ValueError)
    
    def always_fail():
        raise ValueError("Fail")
    
    # Gọi đến threshold
    for _ in range(3):
        with pytest.raises(ValueError):
            cb.call(always_fail)
    
    assert cb.state == "OPEN"
    
    # Lần gọi tiếp theo bị block
    with pytest.raises(Exception, match="Circuit breaker OPEN"):
        cb.call(always_fail)

def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker chuyển sang HALF_OPEN sau timeout."""
    cb = CircuitBreaker(failure_threshold=2, timeout=0.5, expected_exception=ValueError)
    
    def fail_then_succeed():
        raise ValueError("Fail")
    
    # Open circuit
    for _ in range(2):
        with pytest.raises(ValueError):
            cb.call(fail_then_succeed)
    
    assert cb.state == "OPEN"
    
    # Chờ timeout
    time.sleep(0.6)
    
    # Mock success function
    def succeed():
        return "ok"
    
    # Nên chuyển sang HALF_OPEN và thành công
    result = cb.call(succeed)
    assert result == "ok"
    assert cb.state == "CLOSED"
