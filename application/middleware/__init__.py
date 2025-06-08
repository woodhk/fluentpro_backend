"""
Application middleware package.

Contains middleware components for request processing, correlation tracking,
and cross-cutting concerns.
"""

from .correlation_id import CorrelationIdMiddleware

__all__ = [
    'CorrelationIdMiddleware',
]