from uuid import UUID
from arq import Retry
from app.infrastructure.uow import SqlAlchemyUoW
from app.infrastructure.provider_fal import FalProvider
from app.infrastructure.provider_failover import FailoverProvider
from app.settings import settings
from app.domain.enums import GenerationStatus
from app.infrastructure.metrics import generation_total, provider_errors_total, generation_cost_total
from app.infrastructure.webhook_delivery import enqueue_webhook

def _provider():
    primary = FalProvider(settings.fal_api_key_primary)
    secondary = FalProvider(settings.fal_api_key_secondary) if settings.fal_api_key_secondary else None
    return FailoverProvider(primary, secondary)

async def submit_generation(ctx, generation_id: str, provider_callback_base: str):
    gen_id = UUID(generation_id)
    provider = _provider()

    async with SqlAlchemyUoW() as uow:
        gen = await uow.generations.get(gen_id)
        if not gen:
            return
        user = await uow.users.get(gen.user_id)
        if not user:
            return

        try:
            webhook_url = f"{provider_callback_base}/generations/providers/fal/webhook"
            submission = await provider.submit(
                kind=gen.kind,
                prompt=gen.prompt,
                input_image_url=gen.input_image_url,
                webhook_url=webhook_url,
                idempotency_key=str(gen.id),
            )
            gen.mark_queued(submission.request_id)
            await uow.generations.save(gen)
            await uow.commit()
        except Exception as e:
            provider_errors_total.labels(provider="fal").inc()
            gen.mark_failed(str(e))
            if user.wallet.reserved_tokens >= gen.cost_tokens:
                user.wallet.refund_reserved(gen.cost_tokens)

            await uow.users.save(user)
            await uow.generations.save(gen)
            await uow.commit()
            generation_total.labels(kind=gen.kind.value, status="failed").inc()
            raise Retry(defer=3)


async def poll_generation(ctx, generation_id: str):
    gen_id = UUID(generation_id)
    provider = _provider()
    async with SqlAlchemyUoW() as uow:
        gen = await uow.generations.get(gen_id)
        if not gen or not gen.provider_request_id:
            return
        user = await uow.users.get(gen.user_id)
        if not user:
            return

        if gen.status in (GenerationStatus.COMPLETED, GenerationStatus.FAILED):
            return

        try:
            st = await provider.get_status(request_id=gen.provider_request_id)
        except Exception:
            provider_errors_total.labels(provider="fal").inc()
            raise Retry(defer=10)

        if st.status == "queued":
            gen.status = GenerationStatus.QUEUED
        elif st.status == "processing":
            gen.status = GenerationStatus.PROCESSING
        elif st.status == "completed":
            gen.mark_completed(st.result_url or "")
            user.wallet.commit_spend(gen.cost_tokens)
            generation_cost_total.labels(kind=gen.kind.value).inc(gen.cost_tokens)
            generation_total.labels(kind=gen.kind.value, status="completed").inc()
            if gen.callback_url:
                await enqueue_webhook(gen.callback_url, {
                    "generation_id": str(gen.id),
                    "status": "completed",
                    "result_url": gen.result_url,
                })
        elif st.status == "failed":
            gen.mark_failed(st.error or "failed")
            if user.wallet.reserved_tokens >= gen.cost_tokens:
                user.wallet.refund_reserved(gen.cost_tokens)
            generation_total.labels(kind=gen.kind.value, status="failed").inc()
            if gen.callback_url:
                await enqueue_webhook(gen.callback_url, {
                    "generation_id": str(gen.id),
                    "status": "failed",
                    "error": gen.error,
                })

        await uow.generations.save(gen)
        await uow.users.save(user)
        await uow.commit()

        if gen.status not in (GenerationStatus.COMPLETED, GenerationStatus.FAILED):
            raise Retry(defer=10)
