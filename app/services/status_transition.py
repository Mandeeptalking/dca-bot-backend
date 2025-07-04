from datetime import datetime, timezone
from app.supabase_client import supabase

def uses_webhook(bot_id: str) -> bool:
    try:
        response = (
            supabase.table("bots")
            .select("entry_webhook")
            .eq("bot_id", bot_id)
            .single()
            .execute()
        )
        if getattr(response, "error", None):
            print(f"⚠️ Error checking webhook config: {response.error}")  # type: ignore
            return False
        is_webhook = response.data.get("entry_webhook", False)
        print(f"🔎 Bot {bot_id} uses_webhook = {is_webhook}")
        return is_webhook
    except Exception as e:
        print(f"❌ Exception in uses_webhook(): {e}")
        return False

def update_bot_status(bot_id: str, new_status: str):
    try:
        update_payload = {
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        response = (
            supabase.table("bots")
            .update(update_payload)
            .eq("bot_id", bot_id)
            .execute()
        )

        if getattr(response, "error", None):
            print(f"❌ Failed to update bot status: {response.error}")  # type: ignore
        else:
            print(f"✅ Bot status updated to '{new_status}' for bot_id={bot_id}")
    except Exception as e:
        print(f"❌ Exception while updating bot status for bot_id={bot_id}: {e}")

def log_bot_event(run_id: str, bot_id: str, user_id: str, event_type: str, metadata: dict = {}):
    try:
        payload = {
            "run_id": run_id,
            "bot_id": bot_id,
            "user_id": user_id,
            "event": event_type,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        response = supabase.table("bot_logs").insert(payload).execute()
        if getattr(response, "error", None):
            print(f"❌ Failed to log bot event '{event_type}': {getattr(response, 'error', 'Unknown error')}")
        else:
            print(f"📋 Logged bot event: {event_type}")
    except Exception as e:
        print(f"❌ Exception while logging bot event '{event_type}': {e}")

def update_bot_run_status(run_id: str, new_status: str):
    try:
        response = (
            supabase.table("bot_runs")
            .update({
                "status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            .eq("run_id", run_id)
            .execute()
        )
        if getattr(response, "error", None):
            print(f"❌ Failed to update bot_run status: {getattr(response, 'error', 'Unknown error')}")
        else:
            print(f"✅ Bot run status updated to '{new_status}' for run_id={run_id}")
    except Exception as e:
        print(f"❌ Exception while updating bot run status: {e}")

def get_latest_run_id(bot_id: str):
    try:
        response = (
            supabase.table("bot_runs")
            .select("run_id, status")
            .eq("bot_id", bot_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        if getattr(response, "error", None):
            print(f"❌ Failed to fetch latest run_id: {getattr(response, 'error', 'Unknown error')}")
            return None
        if not response.data:
            return None
        return response.data[0]["run_id"]
    except Exception as e:
        print(f"❌ Exception while fetching latest run_id: {e}")
        return None

def start_bot_run(bot_id: str, user_id: str):
    """Create a new run or fetch the existing latest run.
    - Webhook bots: status = 'waiting'
    - Normal bots: status = 'running'
    """
    try:
        latest_response = (
            supabase.table("bot_runs")
            .select("run_id, status")
            .eq("bot_id", bot_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        if latest_response.data and latest_response.data[0]["status"] == "waiting":
            print(f"🔁 Reusing existing 'waiting' run: {latest_response.data[0]['run_id']}")
            return latest_response.data[0]["run_id"]

        now_utc = datetime.now(timezone.utc).isoformat()
        is_webhook = uses_webhook(bot_id)
        new_status = "waiting" if is_webhook else "running"

        run_payload = {
            "bot_id": bot_id,
            "user_id": user_id,
            "status": new_status,
            "started_at": now_utc
        }

        insert_response = supabase.table("bot_runs").insert(run_payload).execute()
        if insert_response.data:
            run_id = insert_response.data[0]["run_id"]
            print(f"✅ New run started: {run_id} with status '{new_status}'")
            return run_id
        else:
            print("❌ Failed to insert new bot run.")
            return None
    except Exception as e:
        print(f"❌ Exception in start_bot_run: {e}")
        return None
