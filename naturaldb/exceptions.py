"""
Custom exceptions and error handling for NaturalDB
Defines application-specific exceptions and error handling utilities.
"""

from typing import Any, Dict, Optional
import traceback
import sys


class NaturalDBError(Exception):
    """Base exception class for NaturalDB."""
    
    def __init__(self, message: str, error_code: str | None = None, details: Dict[str, Any] | None = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationError(NaturalDBError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str | None = None, value: Any = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        
        super().__init__(message, "VALIDATION_ERROR", details)


class StorageError(NaturalDBError):
    """Raised when storage operations fail."""
    
    def __init__(self, message: str, operation: str | None = None, path: str | None = None):
        details = {}
        if operation:
            details["operation"] = operation
        if path:
            details["path"] = path
        
        super().__init__(message, "STORAGE_ERROR", details)


class QueryError(NaturalDBError):
    """Raised when query operations fail."""
    
    def __init__(self, message: str, query_type: str | None = None, collection: str | None = None):
        details = {}
        if query_type:
            details["query_type"] = query_type
        if collection:
            details["collection"] = collection
        
        super().__init__(message, "QUERY_ERROR", details)


class JSONParseError(NaturalDBError):
    """Raised when JSON parsing fails."""
    
    def __init__(self, message: str, position: int | None = None, content: str | None = None):
        details = {}
        if position is not None:
            details["position"] = position
        if content:
            details["content_preview"] = content[:100] + "..." if len(content) > 100 else content
        
        super().__init__(message, "JSON_PARSE_ERROR", details)


class AuthorizationError(NaturalDBError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, user_id: str | None = None, operation: str | None = None):
        details = {}
        if user_id:
            details["user_id"] = user_id
        if operation:
            details["operation"] = operation
        
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class RecordNotFoundError(NaturalDBError):
    """Raised when a requested record is not found."""
    
    def __init__(self, message: str, collection: str | None = None, record_id: str | None = None):
        details = {}
        if collection:
            details["collection"] = collection
        if record_id:
            details["record_id"] = record_id
        
        super().__init__(message, "RECORD_NOT_FOUND", details)


class CollectionNotFoundError(NaturalDBError):
    """Raised when a requested collection is not found."""
    
    def __init__(self, message: str, collection: str | None = None, user_id: str | None = None):
        details = {}
        if collection:
            details["collection"] = collection
        if user_id:
            details["user_id"] = user_id
        
        super().__init__(message, "COLLECTION_NOT_FOUND", details)


class LockError(NaturalDBError):
    """Raised when file locking operations fail."""
    
    def __init__(self, message: str, resource: str | None = None):
        details = {}
        if resource:
            details["resource"] = resource
        
        super().__init__(message, "LOCK_ERROR", details)


class ConfigurationError(NaturalDBError):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str, config_key: str | None = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(message, "CONFIGURATION_ERROR", details)


class NLPError(NaturalDBError):
    """Raised when natural language processing fails."""
    
    def __init__(self, message: str, query: str | None = None, model: str | None = None):
        details = {}
        if query:
            details["query"] = query[:200] + "..." if len(query) > 200 else query
        if model:
            details["model"] = model
        
        super().__init__(message, "NLP_ERROR", details)


def handle_exception(func):
    """
    Decorator to handle exceptions and convert them to NaturalDB errors.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function that handles exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NaturalDBError:
            # Re-raise NaturalDB errors as-is
            raise
        except (IOError, OSError) as e:
            raise StorageError(f"File operation failed: {e}", operation=func.__name__)
        except ValueError as e:
            raise ValidationError(f"Value error in {func.__name__}: {e}")
        except KeyError as e:
            raise ValidationError(f"Missing required key: {e}")
        except Exception as e:
            # Convert unexpected exceptions to generic NaturalDB errors
            raise NaturalDBError(
                f"Unexpected error in {func.__name__}: {e}",
                error_code="INTERNAL_ERROR",
                details={"function": func.__name__, "exception_type": type(e).__name__}
            )
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def log_exception(logger, exc: Exception, context: Dict[str, Any] | None = None):
    """
    Log exception with context information.
    
    Args:
        logger: Logger instance
        exc: Exception to log
        context: Additional context information
    """
    context = context or {}
    
    if isinstance(exc, NaturalDBError):
        logger.error(
            f"NaturalDB Error: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "context": context
            }
        )
    else:
        logger.error(
            f"Unexpected Error: {exc}",
            extra={
                "exception_type": type(exc).__name__,
                "context": context,
                "traceback": traceback.format_exc()
            }
        )


def format_error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """
    Format error for API response.
    
    Args:
        error: Exception to format
        include_traceback: Whether to include traceback in response
        
    Returns:
        Formatted error dictionary
    """
    if isinstance(error, NaturalDBError):
        response = error.to_dict()
    else:
        response = {
            "error": type(error).__name__,
            "message": str(error),
            "error_code": "INTERNAL_ERROR",
            "details": {}
        }
    
    if include_traceback:
        response["traceback"] = traceback.format_exc()
    
    return response


def safe_execute(func, *args, default_return=None, logger=None, **kwargs):
    """
    Safely execute a function and handle any exceptions.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        default_return: Value to return if function fails
        logger: Logger to use for error logging
        **kwargs: Keyword arguments for the function
        
    Returns:
        Function result or default_return if function fails
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger:
            log_exception(logger, e, {"function": func.__name__})
        return default_return


class ErrorContext:
    """Context manager for error handling with automatic logging."""
    
    def __init__(self, logger, operation: str, **context):
        self.logger = logger
        self.operation = operation
        self.context = context
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.context["operation"] = self.operation
            log_exception(self.logger, exc_val, self.context)
        return False  # Don't suppress exceptions


def validate_and_raise(condition: bool, error_class: type, message: str, **kwargs):
    """
    Validate a condition and raise an error if it fails.
    
    Args:
        condition: Condition to check
        error_class: Exception class to raise if condition fails
        message: Error message
        **kwargs: Additional arguments for the exception
    """
    if not condition:
        raise error_class(message, **kwargs)