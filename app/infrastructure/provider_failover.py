from app.application.ports.provider import ContentProvider, ProviderSubmission, ProviderResult
from app.domain.enums import GenerationKind
from app.infrastructure.circuit_breaker import CircuitBreaker

class FailoverProvider(ContentProvider):
    def __init__(self, primary: ContentProvider, secondary: ContentProvider | None):
        self.primary = primary
        self.secondary = secondary
        self.cb_primary = CircuitBreaker()
        self.cb_secondary = CircuitBreaker()

    def _pick(self) -> ContentProvider:
        if self.cb_primary.allow():
            return self.primary
        if self.secondary and self.cb_secondary.allow():
            return self.secondary
        return self.primary

    async def submit(self, *, kind: GenerationKind, prompt: str, input_image_url: str | None,
                     webhook_url: str | None, idempotency_key: str) -> ProviderSubmission:
        prov = self._pick()
        try:
            res = await prov.submit(kind=kind, prompt=prompt, input_image_url=input_image_url,
                                    webhook_url=webhook_url, idempotency_key=idempotency_key)
            (self.cb_primary if prov is self.primary else self.cb_secondary).on_success()
            return res
        except Exception:
            (self.cb_primary if prov is self.primary else self.cb_secondary).on_failure()
            if prov is self.primary and self.secondary:
                res = await self.secondary.submit(kind=kind, prompt=prompt, input_image_url=input_image_url,
                                                  webhook_url=webhook_url, idempotency_key=idempotency_key)
                self.cb_secondary.on_success()
                return res
            raise

    async def get_status(self, *, request_id: str) -> ProviderResult:
        try:
            r = await self.primary.get_status(request_id=request_id)
            self.cb_primary.on_success()
            return r
        except Exception:
            self.cb_primary.on_failure()
            if self.secondary:
                r = await self.secondary.get_status(request_id=request_id)
                self.cb_secondary.on_success()
                return r
            raise
