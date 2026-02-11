import time
from collections import deque
from typing import Optional

class RateLimiter:
    """
    Token bucket rate limiter to prevent API abuse.
    Tracks request frequency and enforces configurable limits.
    """
    
    def __init__(self, max_requests_per_minute: int = 30):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum allowed requests per minute
        """
        self.max_requests = max_requests_per_minute
        self.request_times = deque()
        self.last_403_time: Optional[float] = None
        self.consecutive_403_count = 0
        
    def can_make_request(self) -> bool:
        """
        Check if a request can be made without exceeding rate limit.
        
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        
        # Remove requests older than 1 minute
        while self.request_times and (now - self.request_times[0]) > 60:
            self.request_times.popleft()
        
        # Check if we're under the limit
        return len(self.request_times) < self.max_requests
    
    def record_request(self):
        """Record that a request was made."""
        self.request_times.append(time.time())
    
    def record_403_error(self):
        """Record a 403 rate limit error."""
        self.last_403_time = time.time()
        self.consecutive_403_count += 1
    
    def reset_403_counter(self):
        """Reset 403 error counter after successful request."""
        self.consecutive_403_count = 0
    
    def get_backoff_time(self) -> int:
        """
        Calculate exponential backoff time based on consecutive 403 errors.
        
        Returns:
            Seconds to wait before next request
        """
        if self.consecutive_403_count == 0:
            return 0
        
        # Exponential backoff: 30s, 60s, 120s, 300s (5min), 600s (10min)
        backoff_times = [30, 60, 120, 300, 600]
        index = min(self.consecutive_403_count - 1, len(backoff_times) - 1)
        return backoff_times[index]
    
    def should_pause_due_to_403(self) -> bool:
        """
        Check if we should pause due to recent 403 errors.
        
        Returns:
            True if we should pause, False otherwise
        """
        if not self.last_403_time:
            return False
        
        backoff_time = self.get_backoff_time()
        elapsed = time.time() - self.last_403_time
        
        return elapsed < backoff_time
    
    def wait_if_needed(self):
        """
        Wait if necessary to respect rate limits.
        Implements exponential backoff for 403 errors.
        """
        # Check for 403 backoff
        if self.should_pause_due_to_403():
            backoff_time = self.get_backoff_time()
            elapsed = time.time() - self.last_403_time
            remaining = backoff_time - elapsed
            
            if remaining > 0:
                print(f"[WARN] Rate limit backoff: waiting {remaining:.0f}s (403 error #{self.consecutive_403_count})")
                time.sleep(remaining)
        
        # Check regular rate limit
        while not self.can_make_request():
            print("[WAIT] Rate limit reached, waiting 5 seconds...")
            time.sleep(5)
