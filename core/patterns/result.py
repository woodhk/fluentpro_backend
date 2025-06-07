from typing import TypeVar, Generic, Union, Optional
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')

@dataclass
class Success(Generic[T]):
    value: T

@dataclass
class Failure(Generic[E]):
    error: E

Result = Union[Success[T], Failure[E]]

def is_success(result: Result) -> bool:
    return isinstance(result, Success)