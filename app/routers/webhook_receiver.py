from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone
from app.supabase_client import supabase
from app.services.evaluator import evaluate_condition_groups
from app.services.run_dca_bot import trigger_bot_condition
from app.services.status_transition import (
    get_latest_run_id,
    update_bot_run_status,
    log_bot_event,
)

router = APIRouter()


@router.post("/webhook/condition")
async def receive_condition_webhook(request: Request):
    body = await request.json()
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token in payload")
    return await handle_condition_trigger(token)


@router.api_route("/wc/{token}", methods=["GET", "POST"])
async def receive_condition_webhook_url(token: str):
    return await handle_condition_trigger(token)


@router.api_route("/webhook/{token}", methods=["GET", "POST"])
async def receive_condition_webhook_direct(token: str):
    return await handle_condition_trigger(token)


async def handle_condition_trigger(token: str):
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
    condition_id = condition["condition_id"]
    bot_id = condition["bot_id"]
    user_id = condition.get("user_id")
    stage = condition.get("stage", "filter")

    if not user_id:
        bot_resp = (
            supabase.table("bots")
            .select("user_id")
            .eq("bot_id", bot_id)
            .limit(1)
            .execute()
        )
        if not bot_resp.data:
            raise HTTPException(status_code=404, detail="Bot not found for condition")
        user_id = bot_resp.data[0]["user_id"]

    validity_secs = condition.get("validity_secs", 300)

    if condition["status"] == "triggered":
        triggered_at = datetime.fromisoformat(condition["triggered_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = (now - triggered_at).total_seconds()
        if delta < validity_secs:
            return {
                "status": "already_triggered",
                "triggered_at": condition["triggered_at"]
            }

    now_utc = datetime.now(timezone.utc).isoformat()
    update_resp = (
        supabase.table("bot_conditions")
        .update({
            "status": "triggered",
            "triggered_at": now_utc
        })
        .eq("condition_id", condition_id)
        .execute()
    )

    if getattr(update_resp, "error", None):
        raise HTTPException(status_code=500, detail="Failed to update condition")

    log_resp = (
        supabase.table("bot_logs")
        .insert({
            "bot_id": bot_id,
            "user_id": user_id,
            "event": "condition_triggered",
            "metadata": {
                "condition_id": condition_id,
                "triggered_at": now_utc,
                "webhook_token": token
            },
            "timestamp": now_utc
        })
        .execute()
    )

    if getattr(log_resp, "error", None):
        raise HTTPException(status_code=500, detail="Failed to log trigger event")

    if stage in ["trigger", "filter"]:
        print(f"🚀 Trigger stage reached (stage={stage}). Evaluating and executing bot {bot_id}")

        # Optional pre-evaluation
        evaluate_condition_groups(bot_id=bot_id, user_id=user_id)

        # Run the trigger logic
        result = trigger_bot_condition(bot_id, user_id)

        if result:
            print(f"✅ Bot trigger result: {result}")

            # ✅ Update bot_runs.stage = 'executed'
            run_id = get_latest_run_id(bot_id)
            if run_id:
                update_bot_run_status(run_id, "executed")

                log_bot_event(
                    run_id=run_id,
                    bot_id=bot_id,
                    user_id=user_id,
                    event_type="entry_executed",
                    metadata={"source": "webhook_receiver"}
                )
        else:
            print(f"⚠️ Bot trigger returned no result")
    else:
        condition_type = condition.get("type", "setup")
        print(f"⚠️ Condition triggered but ignored due to stage={stage} (expected 'filter' or 'trigger')")

    return {
        "status": "triggered",
        "condition_id": condition_id,
        "triggered_at": now_utc
    }
