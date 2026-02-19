from fastapi import APIRouter
from pydantic import BaseModel
from app.infrastructure.uow import SqlAlchemyUoW
from app.application.use_cases.register_user import register_user, RegisterUserCmd

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterReq(BaseModel):
    external_user_id: str

class RegisterRes(BaseModel):
    api_key: str

@router.post("/register", response_model=RegisterRes)
async def register(req: RegisterReq):
    async with SqlAlchemyUoW() as uow:
        res = await register_user(uow, RegisterUserCmd(external_user_id=req.external_user_id))
        return RegisterRes(api_key=res.api_key)
