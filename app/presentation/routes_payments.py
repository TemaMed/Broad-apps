from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.settings import settings
from app.infrastructure.uow import SqlAlchemyUoW
from app.application.use_cases.topup_balance import topup_balance, TopUpCmd

router = APIRouter(prefix="/payments", tags=["payments"])

class TopupWebhookReq(BaseModel):
    external_user_id: str
    amount: int

@router.post("/webhook")
async def payment_webhook(req: TopupWebhookReq, x_webhook_secret: str = Header(..., alias="X-Webhook-Secret")):
    if x_webhook_secret != settings.payments_webhook_secret:
        raise HTTPException(status_code=403, detail="bad secret")
    async with SqlAlchemyUoW() as uow:
        await topup_balance(uow, TopUpCmd(external_user_id=req.external_user_id, amount=req.amount))
    return {"ok": True}
