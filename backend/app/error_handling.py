"""
Comprehensive Error Handling and Logging System
Version: 2.0
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
import json
import os
from enum import Enum
import uuid
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    FILE_PROCESSING = "file_processing"
    ML_MODEL = "ml_model"
    API = "api"
    SYSTEM = "system"
    NETWORK = "network"
    SECURITY = "security"

class CustomException(Exception):
    """Base custom exception class"""
    def __init__(self, message: str, category: ErrorCategory, severity: ErrorSeverity, 
                 error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.category = category
        self.severity = severity
        self.error_code = error_code or f"ERR_{category.value.upper()}_{severity.value.upper()}"
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        self.error_id = str(uuid.uuid4())
        super().__init__(self.message)

class AuthenticationError(CustomException):
    """Authentication related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, details=details)

class AuthorizationError(CustomException):
    """Authorization related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.AUTHORIZATION, ErrorSeverity.HIGH, details=details)

class ValidationError(CustomException):
    """Validation related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, details=details)

class DatabaseError(CustomException):
    """Database related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.DATABASE, ErrorSeverity.HIGH, details=details)

class FileProcessingError(CustomException):
    """File processing related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.FILE_PROCESSING, ErrorSeverity.MEDIUM, details=details)

class MLModelError(CustomException):
    """ML model related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.ML_MODEL, ErrorSeverity.MEDIUM, details=details)

class APIError(CustomException):
    """API related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.API, ErrorSeverity.MEDIUM, details=details)

class SystemError(CustomException):
    """System related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL, details=details)

class SecurityError(CustomException):
    """Security related errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, ErrorCategory.SECURITY, ErrorSeverity.CRITICAL, details=details)

class ErrorHandler:
    """Comprehensive error handling system"""
    
    def __init__(self):
        self.error_log = []
        self.error_counts = {}
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,
            ErrorSeverity.HIGH: 5,
            ErrorSeverity.MEDIUM: 20,
            ErrorSeverity.LOW: 100
        }
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle and log an error"""
        error_info = self._extract_error_info(error, context)
        self._log_error(error_info)
        self._update_error_counts(error_info)
        self._check_alert_thresholds(error_info)
        
        return error_info
    
    def _extract_error_info(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract comprehensive error information"""
        error_info = {
            'error_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        if isinstance(error, CustomException):
            error_info.update({
                'category': error.category.value,
                'severity': error.severity.value,
                'error_code': error.error_code,
                'details': error.details
            })
        else:
            # Determine category and severity for standard exceptions
            error_info.update(self._classify_standard_exception(error))
        
        return error_info
    
    def _classify_standard_exception(self, error: Exception) -> Dict[str, str]:
        """Classify standard exceptions into categories and severity"""
        error_type = type(error).__name__
        
        if error_type in ['ValueError', 'TypeError', 'AttributeError']:
            return {'category': ErrorCategory.VALIDATION.value, 'severity': ErrorSeverity.MEDIUM.value}
        elif error_type in ['ConnectionError', 'TimeoutError', 'NetworkError']:
            return {'category': ErrorCategory.NETWORK.value, 'severity': ErrorSeverity.HIGH.value}
        elif error_type in ['FileNotFoundError', 'PermissionError', 'OSError']:
            return {'category': ErrorCategory.SYSTEM.value, 'severity': ErrorSeverity.MEDIUM.value}
        elif error_type in ['MemoryError', 'SystemError']:
            return {'category': ErrorCategory.SYSTEM.value, 'severity': ErrorSeverity.CRITICAL.value}
        else:
            return {'category': ErrorCategory.SYSTEM.value, 'severity': ErrorSeverity.MEDIUM.value}
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Log error information"""
        # Add to error log
        self.error_log.append(error_info)
        
        # Log to appropriate level
        severity = error_info.get('severity', 'medium')
        message = f"Error {error_info['error_id']}: {error_info['message']}"
        
        if severity == 'critical':
            logger.critical(message, extra=error_info)
        elif severity == 'high':
            logger.error(message, extra=error_info)
        elif severity == 'medium':
            logger.warning(message, extra=error_info)
        else:
            logger.info(message, extra=error_info)
    
    def _update_error_counts(self, error_info: Dict[str, Any]):
        """Update error counts for monitoring"""
        category = error_info.get('category', 'unknown')
        severity = error_info.get('severity', 'medium')
        
        key = f"{category}_{severity}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    def _check_alert_thresholds(self, error_info: Dict[str, Any]):
        """Check if error thresholds are exceeded"""
        severity = error_info.get('severity', 'medium')
        category = error_info.get('category', 'unknown')
        
        try:
            severity_enum = ErrorSeverity(severity)
            threshold = self.alert_thresholds.get(severity_enum, 100)
            
            key = f"{category}_{severity}"
            count = self.error_counts.get(key, 0)
            
            if count >= threshold:
                self._send_alert(error_info, count, threshold)
        except ValueError:
            pass  # Invalid severity level
    
    def _send_alert(self, error_info: Dict[str, Any], count: int, threshold: int):
        """Send alert for threshold exceeded"""
        alert_message = f"ALERT: {error_info['category']} errors exceeded threshold. " \
                       f"Count: {count}, Threshold: {threshold}"
        
        logger.critical(alert_message, extra={
            'alert_type': 'threshold_exceeded',
            'error_info': error_info,
            'count': count,
            'threshold': threshold
        })
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        total_errors = len(self.error_log)
        
        # Count by category
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_log:
            category = error.get('category', 'unknown')
            severity = error.get('severity', 'unknown')
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_errors': total_errors,
            'category_counts': category_counts,
            'severity_counts': severity_counts,
            'error_counts': self.error_counts,
            'recent_errors': self.error_log[-10:] if self.error_log else []
        }
    
    def clear_error_log(self, older_than_days: int = 7):
        """Clear old error logs"""
        cutoff_date = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
        
        self.error_log = [
            error for error in self.error_log
            if datetime.fromisoformat(error['timestamp']).timestamp() > cutoff_date
        ]

# Global error handler instance
error_handler = ErrorHandler()

def error_handler_decorator(category: ErrorCategory = None, severity: ErrorSeverity = None):
    """Decorator for error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'args': str(args)[:200],  # Limit length
                    'kwargs': str(kwargs)[:200]
                }
                
                error_info = error_handler.handle_error(e, context)
                
                # Re-raise as appropriate exception type
                if category and severity:
                    raise CustomException(
                        message=str(e),
                        category=category,
                        severity=severity,
                        details=error_info
                    )
                else:
                    raise
        
        return wrapper
    return decorator

@contextmanager
def error_context(operation: str, category: ErrorCategory = ErrorCategory.SYSTEM):
    """Context manager for error handling"""
    try:
        yield
    except Exception as e:
        context = {'operation': operation, 'category': category.value}
        error_info = error_handler.handle_error(e, context)
        
        # Re-raise with appropriate context
        if isinstance(e, CustomException):
            raise
        else:
            raise CustomException(
                message=str(e),
                category=category,
                severity=ErrorSeverity.MEDIUM,
                details=error_info
            )

class LoggingConfig:
    """Advanced logging configuration"""
    
    @staticmethod
    def setup_application_logging():
        """Setup application-wide logging"""
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # File handler for all logs
        file_handler = logging.FileHandler('logs/application.log')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    @staticmethod
    def setup_performance_logging():
        """Setup performance logging"""
        perf_logger = logging.getLogger('performance')
        perf_logger.setLevel(logging.INFO)
        
        # Performance file handler
        perf_handler = logging.FileHandler('logs/performance.log')
        perf_formatter = logging.Formatter(
            '%(asctime)s - %(message)s'
        )
        perf_handler.setFormatter(perf_formatter)
        perf_logger.addHandler(perf_handler)
        
        return perf_logger
    
    @staticmethod
    def setup_security_logging():
        """Setup security logging"""
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.INFO)
        
        # Security file handler
        security_handler = logging.FileHandler('logs/security.log')
        security_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        security_handler.setFormatter(security_formatter)
        security_logger.addHandler(security_handler)
        
        return security_logger

class PerformanceLogger:
    """Performance logging utilities"""
    
    def __init__(self):
        self.logger = LoggingConfig.setup_performance_logging()
    
    def log_operation_time(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """Log operation execution time"""
        message = f"Operation: {operation}, Duration: {duration:.4f}s"
        if details:
            message += f", Details: {json.dumps(details)}"
        
        self.logger.info(message)
    
    def log_memory_usage(self, operation: str, memory_mb: float):
        """Log memory usage"""
        self.logger.info(f"Operation: {operation}, Memory: {memory_mb:.2f}MB")
    
    def log_database_query(self, query: str, duration: float, rows_affected: int = None):
        """Log database query performance"""
        message = f"Query: {query[:100]}..., Duration: {duration:.4f}s"
        if rows_affected is not None:
            message += f", Rows: {rows_affected}"
        
        self.logger.info(message)

class SecurityLogger:
    """Security logging utilities"""
    
    def __init__(self):
        self.logger = LoggingConfig.setup_security_logging()
    
    def log_authentication_attempt(self, username: str, success: bool, ip_address: str = None):
        """Log authentication attempts"""
        status = "SUCCESS" if success else "FAILED"
        message = f"Authentication {status} - Username: {username}"
        if ip_address:
            message += f", IP: {ip_address}"
        
        if success:
            self.logger.info(message)
        else:
            self.logger.warning(message)
    
    def log_authorization_failure(self, username: str, resource: str, ip_address: str = None):
        """Log authorization failures"""
        message = f"Authorization FAILED - Username: {username}, Resource: {resource}"
        if ip_address:
            message += f", IP: {ip_address}"
        
        self.logger.warning(message)
    
    def log_suspicious_activity(self, activity: str, details: Dict[str, Any] = None):
        """Log suspicious activities"""
        message = f"Suspicious Activity: {activity}"
        if details:
            message += f", Details: {json.dumps(details)}"
        
        self.logger.warning(message)
    
    def log_security_event(self, event: str, severity: str, details: Dict[str, Any] = None):
        """Log general security events"""
        message = f"Security Event: {event}, Severity: {severity}"
        if details:
            message += f", Details: {json.dumps(details)}"
        
        if severity.upper() == 'CRITICAL':
            self.logger.critical(message)
        elif severity.upper() == 'HIGH':
            self.logger.error(message)
        else:
            self.logger.warning(message)

# Initialize loggers
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()

# Setup application logging
LoggingConfig.setup_application_logging()

# Export commonly used functions and classes
__all__ = [
    'CustomException', 'AuthenticationError', 'AuthorizationError', 'ValidationError',
    'DatabaseError', 'FileProcessingError', 'MLModelError', 'APIError', 'SystemError',
    'SecurityError', 'ErrorHandler', 'error_handler', 'error_handler_decorator',
    'error_context', 'LoggingConfig', 'PerformanceLogger', 'SecurityLogger',
    'performance_logger', 'security_logger'
]
