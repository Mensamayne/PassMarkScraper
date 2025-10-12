"""Retry utilities for scraping."""
import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each attempt
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Result from func
        
    Raises:
        Last exception if all attempts fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            result = func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"Retry successful on attempt {attempt}")
            return result
            
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt}/{max_attempts} failed: {e}")
            
            if attempt < max_attempts:
                logger.info(f"Retrying in {delay}s...")
                time.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_attempts} attempts failed")
    
    raise last_exception

