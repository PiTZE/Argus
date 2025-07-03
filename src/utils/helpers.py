"""Utility functions and helpers."""

import os
import time
import hashlib
import logging
from typing import Any, Dict, List, Optional
from functools import wraps
import streamlit as st

logger = logging.getLogger(__name__)

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_duration(seconds: float) -> str:
    """Format duration in human readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def format_number(number: int) -> str:
    """Format large numbers with commas."""
    return f"{number:,}"

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def generate_cache_key(*args) -> str:
    """Generate a cache key from arguments."""
    content = '|'.join(str(arg) for arg in args)
    return hashlib.md5(content.encode()).hexdigest()

def timing_decorator(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    return wrapper

def error_handler(func):
    """Decorator for consistent error handling in Streamlit."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            st.error(f"❌ An error occurred: {e}")
            return None
    return wrapper

def validate_csv_file(file_path: str) -> Dict[str, Any]:
    """Validate CSV file and return metadata."""
    try:
        import pandas as pd
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {'valid': False, 'error': 'File does not exist'}
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return {'valid': False, 'error': 'File is empty'}
        
        # Try to read first few rows
        try:
            sample_df = pd.read_csv(file_path, nrows=5)
        except Exception as e:
            return {'valid': False, 'error': f'Invalid CSV format: {e}'}
        
        # Check if has columns
        if len(sample_df.columns) == 0:
            return {'valid': False, 'error': 'No columns found'}
        
        return {
            'valid': True,
            'file_size': file_size,
            'columns': list(sample_df.columns),
            'sample_rows': len(sample_df)
        }
        
    except Exception as e:
        return {'valid': False, 'error': f'Validation error: {e}'}

def clean_column_name(column_name: str) -> str:
    """Clean column name for SQL compatibility."""
    # Remove special characters and replace with underscores
    import re
    cleaned = re.sub(r'[^\w\s]', '_', column_name)
    cleaned = re.sub(r'\s+', '_', cleaned)
    cleaned = cleaned.strip('_')
    
    # Ensure it doesn't start with a number
    if cleaned and cleaned[0].isdigit():
        cleaned = f"col_{cleaned}"
    
    return cleaned or "unnamed_column"

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage information."""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent()
        }
    except ImportError:
        return {'error': 'psutil not available'}
    except Exception as e:
        return {'error': str(e)}

def check_disk_space(path: str = ".") -> Dict[str, float]:
    """Check available disk space."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        
        return {
            'total_gb': total / (1024**3),
            'used_gb': used / (1024**3),
            'free_gb': free / (1024**3),
            'used_percent': (used / total) * 100
        }
    except Exception as e:
        return {'error': str(e)}

def create_progress_callback(progress_bar, status_text):
    """Create a progress callback function for long-running operations."""
    def callback(message: str, progress: Optional[float] = None):
        if status_text:
            status_text.info(message)
        if progress_bar and progress is not None:
            progress_bar.progress(progress)
    
    return callback

def batch_process(items: List[Any], batch_size: int = 100):
    """Process items in batches."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator

class PerformanceMonitor:
    """Monitor performance metrics during operations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.metrics = {}
    
    def __enter__(self):
        self.start_time = time.time()
        self.metrics['start_memory'] = get_memory_usage()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.metrics['duration'] = duration
        self.metrics['end_memory'] = get_memory_usage()
        
        logger.info(f"Performance metrics for {self.operation_name}: {self.metrics}")
        
        if exc_type is not None:
            logger.error(f"Operation {self.operation_name} failed after {duration:.2f}s")
    
    def add_metric(self, key: str, value: Any):
        """Add a custom metric."""
        self.metrics[key] = value

def streamlit_cache_key(*args, **kwargs) -> str:
    """Generate a cache key for Streamlit caching."""
    import json
    
    # Convert args and kwargs to a hashable string
    cache_data = {
        'args': args,
        'kwargs': kwargs
    }
    
    try:
        cache_string = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.md5(cache_string.encode()).hexdigest()
    except Exception:
        # Fallback to simple string concatenation
        return hashlib.md5(str(cache_data).encode()).hexdigest()