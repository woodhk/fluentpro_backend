from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

TRequest = TypeVar('TRequest', bound=BaseModel)
TResponse = TypeVar('TResponse', bound=BaseModel)

class UseCase(ABC, Generic[TRequest, TResponse]):
    """Base use case following command pattern"""
    
    @abstractmethod
    async def execute(self, request: TRequest) -> TResponse:
        """Execute the use case with given request"""
        pass
    
    async def __call__(self, request: TRequest) -> TResponse:
        """Allow use case to be called as function"""
        return await self.execute(request)

class NoRequestUseCase(ABC, Generic[TResponse]):
    """Use case that doesn't require input"""
    
    @abstractmethod
    async def execute(self) -> TResponse:
        pass