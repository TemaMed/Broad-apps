from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, AnyHttpUrl
from uuid import UUID
from urllib.parse import urlparse
from arq import create_pool
from arq.connections import RedisSettings
from app.settings import settings
from app.presentation.deps import auth_user
from app.infrastructure.uow import SqlAlchemyUoW
from app.domain.generation import Generation
from app.domain.enums import GenerationKind
from app.application.pricing import estimate_cost_tokens

router = APIRouter(prefix="/generations", tags=["generations"])

class CreateImageReq(BaseModel):
    prompt: str
    input_image_url: AnyHttpUrl | None = None
    callback_url: AnyHttpUrl | None = None

class CreateVideoReq(BaseModel):
    prompt: str
    input_image_url: AnyHttpUrl | None = None
    callback_url: AnyHttpUrl | None = None
    seconds: int | None = 5
    resolution: str | None = "480p"

class CreateRes(BaseModel):
    generation_id: UUID
    status: str

class GenRes(BaseModel):
    id: UUID
    kind: str
    status: str
    result_url: str | None
    error: str | None
    cost_tokens: int

def _redis_settings_from_dsn(dsn: str) -> RedisSettings:
    u = urlparse(dsn)
    db = int((u.path or "/0").lstrip("/"))
    return RedisSettings(host=u.hostname or "redis", port=u.port or 6379, database=db, password=u.password)

async def _enqueue(task_name: str, *args):
    pool = await create_pool(_redis_settings_from_dsn(settings.redis_dsn))
    try:
        await pool.enqueue_job(task_name, *args)
    finally:
        res = pool.close()
        if hasattr(res, "__await__"):  # close может быть awaitable
            await res


@router.post("/images", response_model=CreateRes)
async def create_image(req: CreateImageReq, user=Depends(auth_user)):
    cost = estimate_cost_tokens(GenerationKind.IMAGE)
    async with SqlAlchemyUoW() as uow:
        db_user = await uow.users.get(user.id)
        if not db_user:
            raise HTTPException(401, "no user")
        w = db_user.ensure_wallet()
        try:
            w.reserve(cost)
        except Exception:
            raise HTTPException(402, "insufficient funds")

        gen = Generation.create(
            user_id=db_user.id,
            kind=GenerationKind.IMAGE,
            prompt=req.prompt,
            input_image_url=str(req.input_image_url) if req.input_image_url else None,
            cost_tokens=cost,
            callback_url=str(req.callback_url) if req.callback_url else None,
        )
        await uow.generations.add(gen)
        await uow.users.save(db_user)
        await uow.commit()

    await _enqueue("submit_generation", str(gen.id), "http://api:8000")
    await _enqueue("poll_generation", str(gen.id))
    return CreateRes(generation_id=gen.id, status=gen.status.value)

@router.post("/videos", response_model=CreateRes)
async def create_video(req: CreateVideoReq, user=Depends(auth_user)):
    cost = estimate_cost_tokens(GenerationKind.VIDEO, seconds=req.seconds, resolution=req.resolution)
    async with SqlAlchemyUoW() as uow:
        db_user = await uow.users.get(user.id)
        if not db_user:
            raise HTTPException(401, "no user")
        w = db_user.ensure_wallet()
        try:
            w.reserve(cost)
        except Exception:
            raise HTTPException(402, "insufficient funds")

        gen = Generation.create(
            user_id=db_user.id,
            kind=GenerationKind.VIDEO,
            prompt=req.prompt,
            input_image_url=str(req.input_image_url) if req.input_image_url else None,
            cost_tokens=cost,
            callback_url=str(req.callback_url) if req.callback_url else None,
        )
        await uow.generations.add(gen)
        await uow.users.save(db_user)
        await uow.commit()

    await _enqueue("submit_generation", str(gen.id), "http://api:8000")
    await _enqueue("poll_generation", str(gen.id))
    return CreateRes(generation_id=gen.id, status=gen.status.value)

@router.get("/{generation_id}", response_model=GenRes)
async def get_generation(generation_id: UUID, user=Depends(auth_user)):
    async with SqlAlchemyUoW() as uow:
        gen = await uow.generations.get(generation_id)
        if not gen or gen.user_id != user.id:
            raise HTTPException(404, "not found")
        return GenRes(
            id=gen.id, kind=gen.kind.value, status=gen.status.value,
            result_url=gen.result_url, error=gen.error, cost_tokens=gen.cost_tokens
        )

@router.post("/providers/fal/webhook")
async def fal_webhook(payload: dict):
    request_id = payload.get("request_id") or payload.get("requestId")
    if not request_id:
        return {"ok": True}

    async with SqlAlchemyUoW() as uow:
        gen = await uow.generations.get_by_provider_request_id(request_id)
        if not gen:
            return {"ok": True}

    await _enqueue("poll_generation", str(gen.id))
    return {"ok": True}
