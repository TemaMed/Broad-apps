from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class GenerationCreated:
    generation_id: UUID

@dataclass(frozen=True)
class GenerationStatusChanged:
    generation_id: UUID
    status: str

@dataclass(frozen=True)
class GenerationCompleted:
    generation_id: UUID

@dataclass(frozen=True)
class GenerationFailed:
    generation_id: UUID
    reason: str
