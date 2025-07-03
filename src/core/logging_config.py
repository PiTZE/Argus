"""Logging configuration for the CSV Search App."""

import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_file: str = "logs/app.log"):
    """Set up logging configuration."""
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Performance logger for search operations
    perf_logger = logging.getLogger('performance')
    perf_handler = logging.handlers.RotatingFileHandler(
        'logs/performance.log', maxBytes=5*1024*1024, backupCount=3
    )
    perf_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(message)s'
    ))
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)
    
    return root_logger

class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
    
    def log_search(self, search_term: str, column: str, files_count: int, 
                   results_count: int, duration: float, user: str = "unknown"):
        """Log search performance metrics."""
        self.logger.info(
            f"SEARCH|user:{user}|term:{search_term}|column:{column}|"
            f"files:{files_count}|results:{results_count}|duration:{duration:.2f}s"
        )
    
    def log_file_processing(self, file_path: str, operation: str, 
                           duration: float, success: bool):
        """Log file processing metrics."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"FILE_PROCESSING|file:{os.path.basename(file_path)}|"
            f"operation:{operation}|duration:{duration:.2f}s|status:{status}"
        )
    
    def log_database_operation(self, operation: str, table: str, 
                              duration: float, rows_affected: int = 0):
        """Log database operation metrics."""
        self.logger.info(
            f"DATABASE|operation:{operation}|table:{table}|"
            f"duration:{duration:.2f}s|rows:{rows_affected}"
        )

# Global performance logger instance
perf_logger = PerformanceLogger()