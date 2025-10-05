"""
Logging utilities for NaturalDB
Provides centralized logging configuration and utilities.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to the levelname
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            )
        
        return super().format(record)


class ContextFilter(logging.Filter):
    """Filter that adds context information to log records."""
    
    def __init__(self, context: Dict[str, Any] | None = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record):
        # Add context information to the record
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class DatabaseLogHandler(logging.Handler):
    """Custom log handler that could store logs in the database (future enhancement)."""
    
    def __init__(self):
        super().__init__()
        self.logs = []  # In-memory storage for now
    
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created),
            'level': record.levelname,
            'message': self.format(record),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra context if available
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = getattr(record, 'user_id')
        if hasattr(record, 'operation'):
            log_entry['operation'] = getattr(record, 'operation')
        if hasattr(record, 'collection'):
            log_entry['collection'] = getattr(record, 'collection')
        
        self.logs.append(log_entry)
        
        # Keep only last 1000 logs to prevent memory issues
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
    
    def get_recent_logs(self, count: int = 100) -> list:
        """Get recent log entries."""
        return self.logs[-count:]


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    include_colors: bool = True
) -> logging.Logger:
    """
    Set up centralized logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        log_to_file: Whether to log to files
        log_to_console: Whether to log to console
        max_file_size: Maximum size of each log file
        backup_count: Number of backup log files to keep
        include_colors: Whether to use colored output for console
        
    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    if log_to_file:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("naturaldb")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(module)s:%(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        if include_colors and sys.stdout.isatty():
            # Use colored formatter for console
            colored_formatter = ColoredFormatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(colored_formatter)
        else:
            console_handler.setFormatter(simple_formatter)
        
        logger.addHandler(console_handler)
    
    # File handlers
    if log_to_file:
        # Main log file (all levels)
        main_log_file = os.path.join(log_dir, "naturaldb.log")
        main_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        main_handler.setLevel(logging.DEBUG)
        main_handler.setFormatter(detailed_formatter)
        logger.addHandler(main_handler)
        
        # Error log file (errors and critical only)
        error_log_file = os.path.join(log_dir, "naturaldb_errors.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    # Add database log handler for in-memory storage
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.INFO)
    db_handler.setFormatter(detailed_formatter)
    logger.addHandler(db_handler)
    
    # Store reference to db_handler for later access
    setattr(logger, 'db_handler', db_handler)
    
    return logger


def get_logger(name: str = "naturaldb") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_operation(logger: logging.Logger, operation: str, **context):
    """
    Decorator to automatically log function operations.
    
    Args:
        logger: Logger instance
        operation: Operation name
        **context: Additional context information
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Add context filter
            context_filter = ContextFilter({
                'operation': operation,
                **context
            })
            logger.addFilter(context_filter)
            
            try:
                logger.info(f"Starting operation: {operation}")
                result = func(*args, **kwargs)
                logger.info(f"Completed operation: {operation}")
                return result
            except Exception as e:
                logger.error(f"Failed operation: {operation} - {e}")
                raise
            finally:
                logger.removeFilter(context_filter)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


def create_child_logger(parent_logger: logging.Logger, name: str) -> logging.Logger:
    """
    Create a child logger with the same configuration as parent.
    
    Args:
        parent_logger: Parent logger
        name: Child logger name
        
    Returns:
        Child logger instance
    """
    child_logger = logging.getLogger(f"{parent_logger.name}.{name}")
    child_logger.setLevel(parent_logger.level)
    
    # Copy handlers from parent
    for handler in parent_logger.handlers:
        child_logger.addHandler(handler)
    
    return child_logger


def log_performance(logger: logging.Logger, threshold_seconds: float = 1.0):
    """
    Decorator to log performance metrics for slow operations.
    
    Args:
        logger: Logger instance
        threshold_seconds: Log warning if operation takes longer than this
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                if duration > threshold_seconds:
                    logger.warning(
                        f"Slow operation detected: {func.__name__} took {duration:.2f} seconds"
                    )
                else:
                    logger.debug(
                        f"Operation completed: {func.__name__} took {duration:.2f} seconds"
                    )
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator


def get_log_stats(logger: logging.Logger) -> Dict[str, Any]:
    """
    Get logging statistics.
    
    Args:
        logger: Logger instance
        
    Returns:
        Dictionary with logging statistics
    """
    stats = {
        'logger_name': logger.name,
        'log_level': logging.getLevelName(logger.level),
        'handlers_count': len(logger.handlers),
        'handlers': []
    }
    
    for handler in logger.handlers:
        handler_info = {
            'type': type(handler).__name__,
            'level': logging.getLevelName(handler.level)
        }
        
        if isinstance(handler, logging.FileHandler):
            handler_info['file'] = handler.baseFilename
        
        if hasattr(handler, 'logs'):  # DatabaseLogHandler
            handler_info['logs_count'] = str(len(getattr(handler, 'logs')))
        
        stats['handlers'].append(handler_info)
    
    return stats


# Global logger instance
_global_logger: Optional[logging.Logger] = None


def init_global_logger(**kwargs) -> logging.Logger:
    """
    Initialize global logger instance.
    
    Args:
        **kwargs: Arguments to pass to setup_logging
        
    Returns:
        Global logger instance
    """
    global _global_logger
    _global_logger = setup_logging(**kwargs)
    return _global_logger


def get_global_logger() -> logging.Logger:
    """
    Get global logger instance.
    
    Returns:
        Global logger instance (creates default if none exists)
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = setup_logging()
    return _global_logger