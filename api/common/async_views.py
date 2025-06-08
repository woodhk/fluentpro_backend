"""
Async view base classes for AI-powered features requiring real-time data flow.
"""

import asyncio
from typing import Any, Optional
from asgiref.sync import sync_to_async
from django.http import HttpRequest
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.authentication import BaseAuthentication
from pydantic import ValidationError

from core.exceptions import (
    ValidationError as DomainValidationError,
    AuthenticationError,
    ConflictError,
    BusinessLogicError
)


class AsyncAPIView(APIView):
    """
    Async-compatible API view for handling async operations with DRF.
    
    Provides async authentication, permission checking, and use case execution
    while maintaining compatibility with DRF's synchronous framework.
    """
    
    async def async_dispatch(self, request: HttpRequest, *args, **kwargs):
        """
        Async dispatch method that handles authentication, permissions, and routing.
        
        This method should be called from the synchronous dispatch method
        to handle async operations properly.
        """
        try:
            # Async authentication
            await self.async_check_permissions(request)
            
            # Route to the appropriate async handler
            handler = getattr(self, f'async_{request.method.lower()}', None)
            if handler:
                return await handler(request, *args, **kwargs)
            else:
                # Fall back to sync handler if no async version exists
                return await sync_to_async(
                    getattr(self, request.method.lower(), self.http_method_not_allowed)
                )(request, *args, **kwargs)
                
        except Exception as e:
            return await self.async_handle_exception(e)
    
    async def async_check_permissions(self, request: HttpRequest):
        """
        Async permission checking that works with both sync and async permissions.
        """
        # Convert sync permission checks to async
        for permission in self.get_permissions():
            if hasattr(permission, 'async_has_permission'):
                # Custom async permission
                has_perm = await permission.async_has_permission(request, self)
            else:
                # Convert sync permission to async
                has_perm = await sync_to_async(permission.has_permission)(request, self)
            
            if not has_perm:
                self.permission_denied(
                    request, 
                    message=getattr(permission, 'message', None),
                    code=getattr(permission, 'code', None)
                )
    
    async def async_handle_exception(self, exc: Exception) -> Response:
        """Handle exceptions in async context with proper error responses."""
        if isinstance(exc, ValidationError):
            return Response(
                {"errors": exc.errors()},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, DomainValidationError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, AuthenticationError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(exc, ConflictError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_409_CONFLICT
            )
        elif isinstance(exc, BusinessLogicError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        else:
            return Response(
                {"error": "Internal server error", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def async_handle_use_case(self, use_case, request_data=None):
        """Execute use case asynchronously with standard error handling."""
        try:
            if request_data is not None:
                response = await use_case.execute(request_data)
            else:
                response = await use_case.execute()
            
            return Response(
                response.dict() if hasattr(response, 'dict') else response,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return await self.async_handle_exception(e)
    
    # Placeholder async HTTP method handlers - override in subclasses
    async def async_get(self, request: HttpRequest, *args, **kwargs):
        """Async GET handler - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_get")
    
    async def async_post(self, request: HttpRequest, *args, **kwargs):
        """Async POST handler - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_post")
    
    async def async_put(self, request: HttpRequest, *args, **kwargs):
        """Async PUT handler - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_put")
    
    async def async_patch(self, request: HttpRequest, *args, **kwargs):
        """Async PATCH handler - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_patch")
    
    async def async_delete(self, request: HttpRequest, *args, **kwargs):
        """Async DELETE handler - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_delete")


class AsyncViewSet(ViewSet):
    """
    Async-compatible ViewSet for CRUD operations with async support.
    
    Provides async versions of standard ViewSet actions while maintaining
    compatibility with DRF's synchronous framework.
    """
    
    async def async_dispatch(self, request: HttpRequest, *args, **kwargs):
        """
        Async dispatch method for ViewSet operations.
        """
        try:
            # Async authentication and permissions
            await self.async_check_permissions(request)
            
            # Determine the action
            action = self.action or getattr(self, 'action', None)
            if action:
                handler = getattr(self, f'async_{action}', None)
                if handler:
                    return await handler(request, *args, **kwargs)
            
            # Fall back to sync methods
            handler = getattr(self, action, None)
            if handler:
                return await sync_to_async(handler)(request, *args, **kwargs)
            else:
                return Response(
                    {"error": "Method not allowed"},
                    status=status.HTTP_405_METHOD_NOT_ALLOWED
                )
                
        except Exception as e:
            return await self.async_handle_exception(e)
    
    async def async_check_permissions(self, request: HttpRequest):
        """Async permission checking for ViewSet."""
        for permission in self.get_permissions():
            if hasattr(permission, 'async_has_permission'):
                has_perm = await permission.async_has_permission(request, self)
            else:
                has_perm = await sync_to_async(permission.has_permission)(request, self)
            
            if not has_perm:
                self.permission_denied(
                    request,
                    message=getattr(permission, 'message', None),
                    code=getattr(permission, 'code', None)
                )
    
    async def async_handle_exception(self, exc: Exception) -> Response:
        """Handle exceptions in async ViewSet context."""
        if isinstance(exc, ValidationError):
            return Response(
                {"errors": exc.errors()},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, DomainValidationError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        elif isinstance(exc, AuthenticationError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        elif isinstance(exc, ConflictError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_409_CONFLICT
            )
        elif isinstance(exc, BusinessLogicError):
            return Response(
                {"error": str(exc)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        else:
            return Response(
                {"error": "Internal server error", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    async def async_handle_use_case(self, use_case, request_data=None):
        """Execute use case asynchronously in ViewSet context."""
        try:
            if request_data is not None:
                response = await use_case.execute(request_data)
            else:
                response = await use_case.execute()
            
            return Response(
                response.dict() if hasattr(response, 'dict') else response,
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return await self.async_handle_exception(e)
    
    # Async CRUD action handlers - override in subclasses
    async def async_list(self, request: HttpRequest, *args, **kwargs):
        """Async list action - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_list")
    
    async def async_create(self, request: HttpRequest, *args, **kwargs):
        """Async create action - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_create")
    
    async def async_retrieve(self, request: HttpRequest, *args, **kwargs):
        """Async retrieve action - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_retrieve")
    
    async def async_update(self, request: HttpRequest, *args, **kwargs):
        """Async update action - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_update")
    
    async def async_partial_update(self, request: HttpRequest, *args, **kwargs):
        """Async partial update action - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_partial_update")
    
    async def async_destroy(self, request: HttpRequest, *args, **kwargs):
        """Async destroy action - override in subclasses."""
        raise NotImplementedError("Subclasses must implement async_destroy")


class AsyncPermission(BasePermission):
    """
    Base class for async permissions.
    
    Provides both sync and async permission checking methods
    for compatibility with both sync and async views.
    """
    
    async def async_has_permission(self, request: HttpRequest, view) -> bool:
        """
        Async permission check - override in subclasses.
        
        By default, falls back to sync has_permission method.
        """
        return await sync_to_async(self.has_permission)(request, view)
    
    async def async_has_object_permission(self, request: HttpRequest, view, obj) -> bool:
        """
        Async object-level permission check - override in subclasses.
        
        By default, falls back to sync has_object_permission method.
        """
        return await sync_to_async(self.has_object_permission)(request, view, obj)


class AsyncAuthentication(BaseAuthentication):
    """
    Base class for async authentication.
    
    Provides async authentication methods for use with async views.
    """
    
    async def async_authenticate(self, request: HttpRequest):
        """
        Async authentication - override in subclasses.
        
        Returns (user, auth) tuple or None.
        """
        return await sync_to_async(self.authenticate)(request)
    
    async def async_authenticate_header(self, request: HttpRequest):
        """
        Async authenticate header - override in subclasses.
        """
        return await sync_to_async(self.authenticate_header)(request)