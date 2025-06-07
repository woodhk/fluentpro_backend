from abc import ABC
from datetime import datetime
from typing import List
from domains.shared.events.base_event import DomainEvent

class BaseEntity(ABC):
    def __init__(self):
        self._domain_events: List[DomainEvent] = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def add_domain_event(self, event: DomainEvent):
        self._domain_events.append(event)
    
    def clear_domain_events(self):
        self._domain_events.clear()
    
    @property
    def domain_events(self) -> List[DomainEvent]:
        return self._domain_events.copy()