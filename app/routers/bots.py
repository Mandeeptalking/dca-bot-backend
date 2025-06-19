from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from app.supabase_client import supabase
from app.services.preflight import validate_bot
from app.services.run_dca_bot import run_dca_bot
from app.services.status_transition import (
    update_bot_status,
    update_bot_run_status,
    log_bot_event,
    get_latest_run_id
)
from app.services.bot_service import delete_bot_completely



router = APIRouter()


# ✅ Get single bot config by bot_id
@router.get("/{bot_id}")
def get_bot(bot_id: str):
    response = (
        supabase
        .table("bots")
        .select("*")
        .eq("bot_id", bot_id)
        .single()
        .execute()
    )
    if not response or not response.data:
        raise HTTPException(status_code=404, detail="Bot not found")
    return response.data

# ✅ Start bot
class StartBotRequest(BaseModel):
    bot_id: str
    user_id: str

@router.post("/start")
def start_bot(request: StartBotRequest):
    print("📥 Received StartBotRequest:", request.dict())

    is_valid, bot, messages = validate_bot(request.bot_id, request.user_id)
    print("✅ Preflight result:", is_valid, messages)

    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": messages})

    try:
        result = run_dca_bot(request.bot_id, request.user_id)
        print("🚀 Bot engine result:", result)
        result["messages"] = messages

        run_id = result.get("run_id")
        if run_id:
            log_bot_event(
                run_id=run_id,
                bot_id=request.bot_id,
                user_id=request.user_id,
                event_type="started"
            )
        else:
            print("⚠️ Warning: run_id is missing from result, skipping log_bot_event.")

        return result
    except Exception as e:
        print("❌ Exception in run_dca_bot:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error: " + str(e))


@router.post("/pause")
def pause_bot(request: StartBotRequest):
    update_bot_status(request.bot_id, "paused")
    run_id = get_latest_run_id(request.bot_id)
    if run_id:
        update_bot_run_status(run_id, "paused")
        log_bot_event(run_id, request.bot_id, request.user_id, "paused")
    else:
        print("⚠️ Warning: No active run_id found, skipping pause log.")
    return {"status": "paused", "message": "Bot paused successfully"}


@router.post("/resume")
def resume_bot(request: StartBotRequest):
    update_bot_status(request.bot_id, "running")
    run_id = get_latest_run_id(request.bot_id)
    if run_id:
        update_bot_run_status(run_id, "running")
        log_bot_event(run_id, request.bot_id, request.user_id, "resumed")
    else:
        print("⚠️ Warning: No active run_id found, skipping resume log.")
    return {"status": "running", "message": "Bot resumed successfully"}



@router.post("/stop")
def stop_bot(request: StartBotRequest):
    update_bot_status(request.bot_id, "stopped")
    run_id = get_latest_run_id(request.bot_id)
    if run_id:
        update_bot_run_status(run_id, "stopped")
        log_bot_event(run_id, request.bot_id, request.user_id, "stopped")
    else:
        print("⚠️ Warning: No active run_id found, skipping stop log.")
    return {"status": "stopped", "message": "Bot stopped successfully"}

@router.delete("/delete")
def delete_bot(request: StartBotRequest):
    try:
        delete_bot_completely(request.bot_id)
        return {"status": "deleted", "message": "Bot and related data deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete bot: {e}")
