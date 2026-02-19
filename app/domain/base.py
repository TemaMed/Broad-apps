from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class Entity:
    id: UUID = field(default_factory=uuid4)

@dataclass
class AggregateRoot(Entity):
    _events: list[object] = field(default_factory=list, init=False, repr=False)

    def pull_events(self) -> list[object]:
        ev, self._events = self._events, []
        return ev

def utcnow() -> datetime:
    return datetime.utcnow()
