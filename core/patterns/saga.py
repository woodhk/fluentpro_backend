from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SagaStep:
    name: str
    action: callable
    compensation: callable

class Saga(ABC):
    """Saga pattern for distributed transactions"""
    
    def __init__(self):
        self.steps: List[SagaStep] = []
        self.executed_steps: List[SagaStep] = []
    
    @abstractmethod
    def define_steps(self) -> List[SagaStep]:
        """Define saga steps"""
        pass
    
    async def execute(self, context: Dict[str, Any]):
        """Execute saga with automatic compensation on failure"""
        self.steps = self.define_steps()
        
        try:
            for step in self.steps:
                result = await step.action(context)
                context[f"{step.name}_result"] = result
                self.executed_steps.append(step)
        except Exception as e:
            # Compensate in reverse order
            for step in reversed(self.executed_steps):
                try:
                    await step.compensation(context)
                except Exception as comp_error:
                    # Log compensation failure
                    pass
            raise e