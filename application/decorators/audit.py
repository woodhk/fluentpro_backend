import functools
import inspect
import logging
from typing import TypeVar, Callable, Optional, Dict, Any
from datetime import datetime
from threading import local

# Thread-local storage for request context
_context = local()

T = TypeVar('T')
logger = logging.getLogger(__name__)

class AuditContext:
    """Context for audit logging"""
    def __init__(self, user_id: str = None, request_id: str = None, ip_address: str = None):
        self.user_id = user_id
        self.request_id = request_id
        self.ip_address = ip_address

def set_audit_context(context: AuditContext):
    """Set audit context for current thread"""
    _context.audit = context

def get_audit_context() -> Optional[AuditContext]:
    """Get audit context for current thread"""
    return getattr(_context, 'audit', None)

def clear_audit_context():
    """Clear audit context for current thread"""
    if hasattr(_context, 'audit'):
        delattr(_context, 'audit')

def audit_log(action: str, resource_type: str):
    """Audit log decorator for tracking user actions"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            context = get_audit_context()
            start_time = datetime.utcnow()
            
            audit_entry = {
                "action": action,
                "resource_type": resource_type,
                "user_id": context.user_id if context else None,
                "request_id": context.request_id if context else None,
                "ip_address": context.ip_address if context else None,
                "timestamp": start_time.isoformat(),
                "function": func.__name__,
                "arguments": _sanitize_args(args, kwargs)
            }
            
            try:
                result = await func(*args, **kwargs)
                audit_entry["status"] = "success"
                audit_entry["duration_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log successful action
                await _save_audit_log(audit_entry)
                
                return result
            except Exception as e:
                audit_entry["status"] = "failure"
                audit_entry["error"] = str(e)
                audit_entry["duration_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log failed action
                await _save_audit_log(audit_entry)
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            context = get_audit_context()
            start_time = datetime.utcnow()
            
            audit_entry = {
                "action": action,
                "resource_type": resource_type,
                "user_id": context.user_id if context else None,
                "request_id": context.request_id if context else None,
                "ip_address": context.ip_address if context else None,
                "timestamp": start_time.isoformat(),
                "function": func.__name__,
                "arguments": _sanitize_args(args, kwargs)
            }
            
            try:
                result = func(*args, **kwargs)
                audit_entry["status"] = "success"
                audit_entry["duration_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log successful action (sync version)
                _save_audit_log_sync(audit_entry)
                
                return result
            except Exception as e:
                audit_entry["status"] = "failure"
                audit_entry["error"] = str(e)
                audit_entry["duration_ms"] = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Log failed action (sync version)
                _save_audit_log_sync(audit_entry)
                
                raise
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def _sanitize_args(args, kwargs):
    """Remove sensitive data from arguments"""
    sensitive_keys = ['password', 'token', 'secret', 'api_key', 'refresh_token', 'access_token']
    sanitized_kwargs = {}
    
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized_kwargs[key] = "***REDACTED***"
        else:
            # Convert to string and truncate long values
            str_value = str(value)
            sanitized_kwargs[key] = str_value[:100] + "..." if len(str_value) > 100 else str_value
    
    return sanitized_kwargs

async def _save_audit_log(audit_entry: Dict[str, Any]):
    """Save audit log entry (async version)"""
    try:
        # For now, just log to the standard logger
        # In production, this could save to database, external service, etc.
        logger.info(f"AUDIT: {audit_entry}")
    except Exception as e:
        logger.error(f"Failed to save audit log: {e}")

def _save_audit_log_sync(audit_entry: Dict[str, Any]):
    """Save audit log entry (sync version)"""
    try:
        # For now, just log to the standard logger
        # In production, this could save to database, external service, etc.
        logger.info(f"AUDIT: {audit_entry}")
    except Exception as e:
        logger.error(f"Failed to save audit log: {e}")