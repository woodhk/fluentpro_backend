from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List

TModel = TypeVar('TModel')
TDto = TypeVar('TDto')

class Mapper(ABC, Generic[TModel, TDto]):
    """Base mapper for model <-> DTO conversion"""
    
    @abstractmethod
    def to_dto(self, model: TModel) -> TDto:
        """Convert model to DTO"""
        pass
    
    @abstractmethod
    def to_model(self, dto: TDto) -> TModel:
        """Convert DTO to model"""
        pass
    
    def to_dto_list(self, models: List[TModel]) -> List[TDto]:
        """Convert list of models to DTOs"""
        return [self.to_dto(model) for model in models]
    
    def to_model_list(self, dtos: List[TDto]) -> List[TModel]:
        """Convert list of DTOs to models"""
        return [self.to_model(dto) for dto in dtos]