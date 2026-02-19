from dataclasses import dataclass
from app.application.ports.provider import ProviderSubmission, ProviderResult
from app.domain.enums import GenerationKind

@dataclass
class DummyProviderState:
    statuses: dict[str, ProviderResult]

class DummyProvider:
    def __init__(self, state: DummyProviderState):
        self.state = state
        self.counter = 0

    async def submit(self, *, kind: GenerationKind, prompt: str, input_image_url: str | None,
                     webhook_url: str | None, idempotency_key: str) -> ProviderSubmission:
        self.counter += 1
        rid = f"req-{self.counter}"
        self.state.statuses[rid] = ProviderResult(status="queued")
        return ProviderSubmission(request_id=rid)

    async def get_status(self, *, request_id: str) -> ProviderResult:
        return self.state.statuses.get(request_id, ProviderResult(status="processing"))
