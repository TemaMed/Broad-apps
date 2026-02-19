from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.domain.enums import GenerationKind

@dataclass(frozen=True)
class ProviderSubmission:
    request_id: str

@dataclass(frozen=True)
class ProviderResult:
    status: str
    result_url: str | None = None
    error: str | None = None

class ContentProvider(ABC):
    @abstractmethod
    async def submit(self, *, kind: GenerationKind, prompt: str, input_image_url: str | None,
                     webhook_url: str | None, idempotency_key: str) -> ProviderSubmission: ...

    @abstractmethod
    async def get_status(self, *, request_id: str) -> ProviderResult: ...
