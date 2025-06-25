from fastapi import APIRouter, Request, HTTPException
from app.supabase_client import supabase
from app.services.run_dca_bot import run_dca_bot
from datetime import datetime

router = APIRouter()

@router.post("/webhook")
async def webhook_handler(request: Request):
    try:
        payload = await request.json()
        bot_id = payload.get("bot_id")
        secret = payload.get("secret")
        signal = payload.get("signal")
        return await process_webhook(bot_id, secret, signal, source="POST")
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.get("/w/{bot_id}/{secret}/{signal}")
async def webhook_url_handler(bot_id: str, secret: str, signal: str):
    try:
        return await process_webhook(bot_id, secret, signal, source="GET")
    except Exception as e:
        print(f"❌ URL-based webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook URL processing failed")


async def process_webhook(bot_id: str, secret: str, signal: str, source: str = "unknown"):
    if not bot_id or not secret or not signal:
        reason = "Missing bot_id, secret, or signal"
        await log_webhook(bot_id, signal, secret, False, reason, source)
        raise HTTPException(status_code=400, detail=reason)

    response = (
        supabase
        .table("bots")
        .select("*")
        .eq("bot_id", bot_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        reason = "Bot not found"
        await log_webhook(bot_id, signal, secret, False, reason, source)
        raise HTTPException(status_code=404, detail=reason)

    bot = response.data[0]

    if bot.get("trigger_mode") != "webhook":
        reason = "Bot is not set to webhook trigger mode"
        await log_webhook(bot_id, signal, secret, False, reason, source)
        raise HTTPException(status_code=403, detail=reason)

    if bot.get("webhook_secret") != secret:
        reason = "Invalid webhook secret"
        await log_webhook(bot_id, signal, secret, False, reason, source)
        raise HTTPException(status_code=401, detail=reason)

    valid_signals = bot.get("webhook_conditions", [])
    if signal not in valid_signals:
        reason = "Signal not recognized for this bot"
        await log_webhook(bot_id, signal, secret, False, reason, source)
        raise HTTPException(status_code=403, detail=reason)

    # ✅ Success – log and run bot
    await log_webhook(bot_id, signal, secret, True, "valid", source)
    result = run_dca_bot(bot_id=bot_id, user_id=bot["user_id"])

    return {
        "status": "success",
        "message": "Bot started successfully from webhook.",
        "details": result
    }


async def log_webhook(bot_id, signal, secret, valid: bool, reason: str, source: str = "unknown"):
    try:
        supabase.table("webhook_logs").insert({
            "bot_id": bot_id,
            "signal": signal,
            "secret": secret,
            "valid": valid,
            "reason": reason,
            "source": source,
            "received_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"❌ Failed to log webhook: {e}")
