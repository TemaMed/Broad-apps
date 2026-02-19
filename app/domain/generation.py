from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from .base import AggregateRoot, utcnow
from .enums import GenerationKind, GenerationStatus
from .events import GenerationCreated, GenerationStatusChanged

@dataclass
class Generation(AggregateRoot):
    user_id: UUID = field(default=None)
    kind: GenerationKind = GenerationKind.IMAGE
    status: GenerationStatus = GenerationStatus.CREATED

    prompt: str = ""
    input_image_url: str | None = None

    provider: str = "fal"
    provider_request_id: str | None = None

    cost_tokens: int = 0
    result_url: str | None = None
    error: str | None = None

    callback_url: str | None = None

    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def mark_queued(self, provider_request_id: str) -> None:
        self.status = GenerationStatus.QUEUED
        self.provider_request_id = provider_request_id
        self.updated_at = utcnow()
        self._events.append(GenerationStatusChanged(self.id, self.status.value))

    def mark_processing(self) -> None:
        self.status = GenerationStatus.PROCESSING
        self.updated_at = utcnow()
        self._events.append(GenerationStatusChanged(self.id, self.status.value))

    def mark_completed(self, result_url: str) -> None:
        self.status = GenerationStatus.COMPLETED
        self.result_url = result_url
        self.error = None
        self.updated_at = utcnow()
        self._events.append(GenerationStatusChanged(self.id, self.status.value))

    def mark_failed(self, reason: str) -> None:
        self.status = GenerationStatus.FAILED
        self.error = reason
        self.updated_at = utcnow()
        self._events.append(GenerationStatusChanged(self.id, self.status.value))

    @staticmethod
    def create(*, user_id: UUID, kind: GenerationKind, prompt: str, input_image_url: str | None,
               cost_tokens: int, callback_url: str | None) -> "Generation":
        g = Generation(
            user_id=user_id, kind=kind, prompt=prompt, input_image_url=input_image_url,
            cost_tokens=cost_tokens, callback_url=callback_url
        )
        g._events.append(GenerationCreated(g.id))
        return g
