from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
from app.supabase_client import supabase
from app.services.evaluator import evaluate_condition_groups

router = APIRouter()

@router.post("/webhook/condition")
async def receive_condition_webhook(request: Request):
    body = await request.json()
    token = body.get("token")

    if not token:
        raise HTTPException(status_code=400, detail="Missing token in payload")

    return await handle_condition_trigger(token)


# ✅ FIXED: Accept both GET and POST from external sources like TradingView
@router.api_route("/wc/{token}", methods=["GET", "POST"])
async def receive_condition_webhook_url(token: str):
    return await handle_condition_trigger(token)


async def handle_condition_trigger(token: str):
    # 1. Lookup matching condition using token
    response = (
        supabase.table("bot_conditions")
        .select("*")
        .eq("webhook_token", token)
        .limit(1)
        .execute()
    )
    data = response.data

    if not data:
        raise HTTPException(status_code=404, detail="Invalid webhook token")

    condition = data[0]
    condition_id = condition["id"]
    bot_id = condition["bot_id"]
    validity_secs = condition.get("validity_secs", 300)

    # 2. Check if already triggered and still within valid duration
    if condition["status"] == "triggered":
        triggered_at = datetime.fromisoformat(condition["triggered_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = (now - triggered_at).total_seconds()
        if delta < validity_secs:
            return {
                "status": "already_triggered",
                "triggered_at": condition["triggered_at"]
            }

    # 3. Update condition as triggered
    now_utc = datetime.now(timezone.utc).isoformat()
    update_resp = (
        supabase.table("bot_conditions")
        .update({
            "status": "triggered",
            "triggered_at": now_utc
        })
        .eq("id", condition_id)
        .execute()
    )

    if getattr(update_resp, "error", None):
        raise HTTPException(status_code=500, detail="Failed to update condition")

    # 4. Log event
    supabase.table("bot_logs").insert({
        "bot_id": bot_id,
        "event": "condition_triggered",
        "metadata": {
            "condition_id": condition_id,
            "triggered_at": now_utc,
            "webhook_token": token
        },
        "timestamp": now_utc
    }).execute()

    # 5. Trigger bot condition group evaluator
    evaluate_condition_groups()

    return {
        "status": "triggered",
        "condition_id": condition_id,
        "triggered_at": now_utc
    }
