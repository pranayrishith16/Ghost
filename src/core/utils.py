# import hashlib
# import time
# import logging
# from typing import List, Any, Callable, Optional
# from pathlib import Path
# from datetime import timedelta
# import functools

# def validate_file_path(file_path: Path, allowed_extensions: List[str] = None) -> bool:
#     """
#     Validate that a file path exists and has an allowed extension.
    
#     Args:
#         file_path: Path to validate
#         allowed_extensions: List of allowed file extensions (e.g., ['.pdf', '.txt'])
    
#     Returns:
#         bool: True if valid, False otherwise
#     """
#     if not file_path.exists():
#         return False
    
#     if not file_path.is_file():
#         return False
    
#     if allowed_extensions:
#         if file_path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
#             return False
    
#     return True

# def calculate_md5_hash(file_path: Path) -> str:
#     """
#     Calculate MD5 hash of a file for integrity checking.
    
#     Args:
#         file_path: Path to the file
    
#     Returns:
#         str: MD5 hash string
#     """
#     hash_md5 = hashlib.md5()
#     with open(file_path, "rb") as f:
#         for chunk in iter(lambda: f.read(4096), b""):
#             hash_md5.update(chunk)
#     return hash_md5.hexdigest()

# def format_timedelta(delta_seconds: float) -> str:
#     """
#     Format a time delta in seconds to a human-readable string.
    
#     Args:
#         delta_seconds: Time difference in seconds
    
#     Returns:
#         str: Formatted time string (e.g., "2h 30m 15s")
#     """
#     delta = timedelta(seconds=delta_seconds)
#     hours, remainder = divmod(delta.seconds, 3600)
#     minutes, seconds = divmod(remainder, 60)
    
#     parts = []
#     if delta.days > 0:
#         parts.append(f"{delta.days}d")
#     if hours > 0:
#         parts.append(f"{hours}h")
#     if minutes > 0:
#         parts.append(f"{minutes}m")
#     if seconds > 0 or not parts:
#         parts.append(f"{seconds}s")
    
#     return " ".join(parts)

# def batch_processing(items: List[Any], batch_size: int, process_func: Callable) -> List[Any]:
#     """
#     Process a list of items in batches.
    
#     Args:
#         items: List of items to process
#         batch_size: Number of items per batch
#         process_func: Function to process each batch
    
#     Returns:
#         List[Any]: Combined results from all batches
#     """
#     results = []
#     total_batches = (len(items) + batch_size - 1) // batch_size
    
#     for i in range(0, len(items), batch_size):
#         batch = items[i:i + batch_size]
#         batch_results = process_func(batch)
#         results.extend(batch_results)
    
#     return results

# def retry_operation(max_retries: int = 3, delay: float = 1.0, 
#                    backoff: float = 2.0, exceptions: tuple = (Exception,)):
#     """
#     Decorator for retrying operations with exponential backoff.
    
#     Args:
#         max_retries: Maximum number of retry attempts
#         delay: Initial delay between retries in seconds
#         backoff: Backoff multiplier (e.g., 2.0 for exponential backoff)
#         exceptions: Tuple of exceptions to catch and retry on
    
#     Returns:
#         Callable: Decorated function
#     """
#     def decorator(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             retries = 0
#             current_delay = delay
#             logger = logging.getLogger(func.__module__)
            
#             while retries <= max_retries:
#                 try:
#                     return func(*args, **kwargs)
#                 except exceptions as e:
#                     retries += 1
#                     if retries > max_retries:
#                         logger.error(f"Operation failed after {max_retries} retries: {e}")
#                         raise
                    
#                     logger.warning(f"Operation failed (attempt {retries}/{max_retries}), "
#                                   f"retrying in {current_delay:.1f}s: {e}")
                    
#                     time.sleep(current_delay)
#                     current_delay *= backoff
            
#             return func(*args, **kwargs)
#         return wrapper
#     return decorator

# def safe_get(dictionary: dict, keys: List[str], default: Any = None) -> Any:
#     """
#     Safely get a nested value from a dictionary without raising KeyError.
    
#     Args:
#         dictionary: Dictionary to search
#         keys: List of keys to traverse
#         default: Default value if any key is not found
    
#     Returns:
#         Any: The found value or default
#     """
#     current = dictionary
#     for key in keys:
#         if isinstance(current, dict) and key in current:
#             current = current[key]
#         else:
#             return default
#     return current

# def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
#     """
#     Split a list into chunks of specified size.
    
#     Args:
#         items: List to chunk
#         chunk_size: Size of each chunk
    
#     Returns:
#         List[List[Any]]: List of chunks
#     """
#     return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]