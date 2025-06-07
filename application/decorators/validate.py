import functools
from typing import TypeVar, Callable, Type, Any
from pydantic import BaseModel, ValidationError
from application.exceptions.domain_exceptions import ValidationException

T = TypeVar('T')

def validate_input(model: Type[BaseModel]):
    """Validate function input using Pydantic model"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                # Validate kwargs against model
                validated_data = model(**kwargs)
                return await func(*args, **validated_data.dict())
            except ValidationError as e:
                raise ValidationException(f"Input validation failed: {str(e)}")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                # Validate kwargs against model
                validated_data = model(**kwargs)
                return func(*args, **validated_data.dict())
            except ValidationError as e:
                raise ValidationException(f"Input validation failed: {str(e)}")
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def validate_output(model: Type[BaseModel]):
    """Validate function output using Pydantic model"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            result = await func(*args, **kwargs)
            
            try:
                # Validate output
                if isinstance(result, dict):
                    validated = model(**result)
                elif hasattr(model, 'from_orm'):
                    validated = model.from_orm(result)
                else:
                    # Try to convert to dict if it has __dict__
                    if hasattr(result, '__dict__'):
                        validated = model(**result.__dict__)
                    else:
                        validated = model(result)
                return validated
            except ValidationError as e:
                raise ValidationException(f"Output validation failed: {str(e)}")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            result = func(*args, **kwargs)
            
            try:
                # Validate output
                if isinstance(result, dict):
                    validated = model(**result)
                elif hasattr(model, 'from_orm'):
                    validated = model.from_orm(result)
                else:
                    # Try to convert to dict if it has __dict__
                    if hasattr(result, '__dict__'):
                        validated = model(**result.__dict__)
                    else:
                        validated = model(result)
                return validated
            except ValidationError as e:
                raise ValidationException(f"Output validation failed: {str(e)}")
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def validate_request(input_model: Type[BaseModel], output_model: Type[BaseModel] = None):
    """Combined input and optional output validation"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply input validation
        validated_func = validate_input(input_model)(func)
        
        # Apply output validation if specified
        if output_model:
            validated_func = validate_output(output_model)(validated_func)
        
        return validated_func
    
    return decorator