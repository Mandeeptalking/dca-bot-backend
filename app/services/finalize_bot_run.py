from datetime import datetime
from uuid import uuid4
from app.supabase_client import supabase

def finalize_bot_run(bot: dict):
    bot_id = bot["bot_id"]
    user_id = bot["user_id"]

    # ✅ Update bot status
    supabase.table("bots") \
        .update({"status": "running"}) \
        .eq("bot_id", bot_id) \
        .execute()

    # ✅ Insert into bot_runs with explicit run_id
    run_id = str(uuid4())
    run_payload = {
        "run_id": run_id,
        "bot_id": bot_id,
        "user_id": user_id,
        "started_at": datetime.utcnow().isoformat(),
        "status": "running"
    }
    supabase.table("bot_runs").insert(run_payload).execute()

    return run_id
