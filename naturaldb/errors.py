"""
Global Error Handling Framework for NaturalDB

This module provides comprehensive error handling capabilities including:
- Custom exception hierarchy with error codes
- Error logging and formatting utilities
- Recovery mechanisms and error context
- Integration with storage and lock systems
"""

import logging
import traceback
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from pathlib import Path


class ErrorCode(Enum):
    """Error codes for different types of failures"""
    # General errors (1000-1099)
    UNKNOWN_ERROR = 1000
    INVALID_ARGUMENT = 1001
    INVALID_STATE = 1002
    CONFIGURATION_ERROR = 1003
    
    # Storage errors (1100-1199)
    STORAGE_INIT_FAILED = 1100
    STORAGE_ACCESS_DENIED = 1101
    STORAGE_CORRUPTED = 1102
    STORAGE_FULL = 1103
    
    # Table errors (1200-1299)
    TABLE_NOT_FOUND = 1200
    TABLE_ALREADY_EXISTS = 1201
    TABLE_ACCESS_DENIED = 1202
    TABLE_CORRUPTED = 1203
    
    # Record errors (1300-1399)
    RECORD_NOT_FOUND = 1300
    RECORD_ALREADY_EXISTS = 1301
    RECORD_CORRUPTED = 1302
    RECORD_TOO_LARGE = 1303
    RECORD_INVALID_FORMAT = 1304
    
    # Lock errors (1400-1499)
    LOCK_ACQUISITION_FAILED = 1400
    LOCK_TIMEOUT = 1401
    LOCK_DEADLOCK_DETECTED = 1402
    LOCK_ALREADY_HELD = 1403
    LOCK_NOT_HELD = 1404
    
    # IO errors (1500-1599)
    FILE_NOT_FOUND = 1500
    FILE_ACCESS_DENIED = 1501
    FILE_CORRUPTED = 1502
    DISK_FULL = 1503
    IO_ERROR = 1504
    
    # Network errors (1600-1699) - for future use
    NETWORK_ERROR = 1600
    CONNECTION_FAILED = 1601
    TIMEOUT_ERROR = 1602
    
    # JSON/Data errors (1700-1799)
    JSON_DECODE_ERROR = 1700
    JSON_ENCODE_ERROR = 1701
    DATA_VALIDATION_ERROR = 1702
    
    # Security errors (1800-1899) - for future use
    AUTHENTICATION_FAILED = 1800
    AUTHORIZATION_FAILED = 1801
    SECURITY_VIOLATION = 1802


@dataclass
class ErrorContext:
    """Context information for error handling and recovery"""
    operation: str = ""
    table: str = ""
    record_id: str = ""
    file_path: str = ""
    user_message: str = ""
    technical_details: Dict[str, Any] = field(default_factory=dict)
    recovery_suggestions: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class NaturalDBError(Exception):
    """Base exception for all NaturalDB errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or ErrorContext()
        self.cause = cause
        self.timestamp = time.time()
    
    def __str__(self) -> str:
        return f"[{self.error_code.name}] {self.message}"
    
    def get_error_details(self) -> Dict[str, Any]:
        """Get comprehensive error details"""
        return {
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "message": self.message,
            "timestamp": self.timestamp,
            "context": {
                "operation": self.context.operation,
                "table": self.context.table,
                "record_id": self.context.record_id,
                "file_path": self.context.file_path,
                "user_message": self.context.user_message,
                "technical_details": self.context.technical_details,
                "recovery_suggestions": self.context.recovery_suggestions,
            },
            "cause": str(self.cause) if self.cause else None,
            "traceback": traceback.format_exc() if self.cause else None
        }


class StorageError(NaturalDBError):
    """Base class for storage-related errors"""
    pass


class TableError(NaturalDBError):
    """Base class for table-related errors"""
    pass


class RecordError(NaturalDBError):
    """Base class for record-related errors"""
    pass


class LockError(NaturalDBError):
    """Base class for lock-related errors"""
    pass


class IOError(NaturalDBError):
    """Base class for I/O-related errors"""
    pass


class DataError(NaturalDBError):
    """Base class for data/JSON-related errors"""
    pass


# Specific error types
class TableNotFoundError(TableError):
    """Raised when a table does not exist"""
    
    def __init__(self, table: str, context: Optional[ErrorContext] = None):
        message = f"Table '{table}' not found"
        if not context:
            context = ErrorContext(
                table=table,
                user_message=f"The table '{table}' does not exist",
                recovery_suggestions=[
                    f"Create the table '{table}' first",
                    "Check if the table name is spelled correctly",
                    "List existing tables to see available options"
                ]
            )
        super().__init__(message, ErrorCode.TABLE_NOT_FOUND, context)


class RecordNotFoundError(RecordError):
    """Raised when a record does not exist"""
    
    def __init__(self, table: str, record_id: str, context: Optional[ErrorContext] = None):
        message = f"Record '{record_id}' not found in table '{table}'"
        if not context:
            context = ErrorContext(
                table=table,
                record_id=record_id,
                user_message=f"The record '{record_id}' does not exist in table '{table}'",
                recovery_suggestions=[
                    f"Check if record ID '{record_id}' is correct",
                    f"List records in table '{table}' to see available IDs",
                    "Create the record if it should exist"
                ]
            )
        super().__init__(message, ErrorCode.RECORD_NOT_FOUND, context)


class RecordAlreadyExistsError(RecordError):
    """Raised when trying to create a record that already exists"""
    
    def __init__(self, table: str, record_id: str, context: Optional[ErrorContext] = None):
        message = f"Record '{record_id}' already exists in table '{table}'"
        if not context:
            context = ErrorContext(
                table=table,
                record_id=record_id,
                user_message=f"A record with ID '{record_id}' already exists in table '{table}'",
                recovery_suggestions=[
                    "Use update operation instead of insert",
                    "Choose a different record ID",
                    "Delete the existing record first if replacement is intended"
                ]
            )
        super().__init__(message, ErrorCode.RECORD_ALREADY_EXISTS, context)


class LockTimeoutError(LockError):
    """Raised when lock acquisition times out"""
    
    def __init__(self, file_path: str, timeout: float, context: Optional[ErrorContext] = None):
        message = f"Lock acquisition timed out after {timeout}s for file: {file_path}"
        if not context:
            context = ErrorContext(
                file_path=file_path,
                technical_details={"timeout": timeout},
                user_message="The operation could not complete due to a lock timeout",
                recovery_suggestions=[
                    "Try the operation again in a moment",
                    "Check if another process is holding the file",
                    "Increase the lock timeout if appropriate"
                ]
            )
        super().__init__(message, ErrorCode.LOCK_TIMEOUT, context)


class DeadlockDetectedError(LockError):
    """Raised when a deadlock is detected"""
    
    def __init__(self, involved_files: List[str], context: Optional[ErrorContext] = None):
        message = f"Deadlock detected involving files: {', '.join(involved_files)}"
        if not context:
            context = ErrorContext(
                technical_details={"involved_files": involved_files},
                user_message="A deadlock was detected and the operation was aborted",
                recovery_suggestions=[
                    "The operation has been automatically retried",
                    "If the problem persists, try operations in a different order",
                    "Contact support if deadlocks occur frequently"
                ]
            )
        super().__init__(message, ErrorCode.LOCK_DEADLOCK_DETECTED, context)


class JSONDecodeError(DataError):
    """Raised when JSON parsing fails"""
    
    def __init__(self, file_path: str, original_error: str, context: Optional[ErrorContext] = None):
        message = f"Failed to decode JSON from file: {file_path}"
        if not context:
            context = ErrorContext(
                file_path=file_path,
                technical_details={"original_error": original_error},
                user_message="The data file appears to be corrupted or contains invalid JSON",
                recovery_suggestions=[
                    "Restore the file from a backup if available",
                    "Manually inspect and fix the JSON syntax",
                    "Delete the corrupted record if data recovery is not possible"
                ]
            )
        super().__init__(message, ErrorCode.JSON_DECODE_ERROR, context)


class FileAccessError(IOError):
    """Raised when file access is denied"""
    
    def __init__(self, file_path: str, operation: str, context: Optional[ErrorContext] = None):
        message = f"Access denied for {operation} operation on file: {file_path}"
        if not context:
            context = ErrorContext(
                file_path=file_path,
                operation=operation,
                user_message=f"Permission denied while trying to {operation} the file",
                recovery_suggestions=[
                    "Check file and directory permissions",
                    "Ensure the process has appropriate access rights",
                    "Try running with elevated permissions if appropriate"
                ]
            )
        super().__init__(message, ErrorCode.FILE_ACCESS_DENIED, context)


class ErrorHandler:
    """Central error handler for NaturalDB operations"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._configure_logging()
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 1000
    
    def _configure_logging(self):
        """Configure logging for error handling"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def handle_error(self, error: NaturalDBError, reraise: bool = True) -> None:
        """Handle and log an error"""
        error_details = error.get_error_details()
        
        # Log the error
        self.logger.error(
            f"Error {error.error_code.name}: {error.message}",
            extra={"error_details": error_details}
        )
        
        # Store in history
        self._add_to_history(error_details)
        
        # Reraise if requested
        if reraise:
            raise error
    
    def _add_to_history(self, error_details: Dict[str, Any]) -> None:
        """Add error to history"""
        self.error_history.append(error_details)
        
        # Trim history if it gets too long
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def get_error_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error history"""
        return self.error_history[-limit:]
    
    def clear_error_history(self) -> None:
        """Clear error history"""
        self.error_history.clear()
    
    def create_context(
        self,
        operation: str = "",
        table: str = "",
        record_id: str = "",
        file_path: str = "",
        **kwargs
    ) -> ErrorContext:
        """Create error context for operations"""
        return ErrorContext(
            operation=operation,
            table=table,
            record_id=record_id,
            file_path=file_path,
            technical_details=kwargs
        )
    
    def wrap_operation(self, operation_name: str, context: Optional[ErrorContext] = None):
        """Decorator to wrap operations with error handling"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                op_context = context or ErrorContext(operation=operation_name)
                try:
                    return func(*args, **kwargs)
                except NaturalDBError:
                    # Re-raise NaturalDB errors as-is
                    raise
                except Exception as e:
                    # Convert other exceptions to NaturalDB errors
                    error = NaturalDBError(
                        message=f"Unexpected error in {operation_name}: {str(e)}",
                        error_code=ErrorCode.UNKNOWN_ERROR,
                        context=op_context,
                        cause=e
                    )
                    self.handle_error(error)
            return wrapper
        return decorator


# Global error handler instance
_global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return _global_error_handler


def handle_error(error: NaturalDBError, reraise: bool = True) -> None:
    """Convenience function to handle errors using global handler"""
    _global_error_handler.handle_error(error, reraise)


def create_context(
    operation: str = "",
    table: str = "",
    record_id: str = "",
    file_path: str = "",
    **kwargs
) -> ErrorContext:
    """Convenience function to create error context"""
    return _global_error_handler.create_context(
        operation, table, record_id, file_path, **kwargs
    )


def error_handler(operation_name: str, context: Optional[ErrorContext] = None):
    """Convenience decorator for error handling"""
    return _global_error_handler.wrap_operation(operation_name, context)