from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.presentation.deps import auth_user

router = APIRouter(prefix="/users", tags=["users"])

class BalanceRes(BaseModel):
    balance_tokens: int
    reserved_tokens: int
    available_tokens: int

@router.get("/me/balance", response_model=BalanceRes)
async def me_balance(user=Depends(auth_user)):
    w = user.ensure_wallet()
    return BalanceRes(
        balance_tokens=w.balance_tokens,
        reserved_tokens=w.reserved_tokens,
        available_tokens=w.available(),
    )
