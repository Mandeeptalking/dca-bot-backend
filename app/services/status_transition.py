# app/services/status_transition.py

from datetime import datetime
from app.supabase_client import supabase


def update_bot_status(bot_id: str, new_status: str):
    try:
        response = (
            supabase.table("bots")
            .update({"status": new_status})
            .eq("bot_id", bot_id)
            .execute()
        )
        if getattr(response, "error", None):
            print(f"❌ Failed to update bot status: {getattr(response, 'error', 'Unknown error')}")
        else:
            print(f"✅ Bot status updated to '{new_status}' for bot_id={bot_id}")
    except Exception as e:
        print(f"❌ Exception while updating bot status: {e}")


def log_bot_event(run_id: str, bot_id: str, user_id: str, event_type: str, metadata: dict = {}):
    try:
        payload = {
            "run_id": run_id,
            "bot_id": bot_id,
            "user_id": user_id,
            "event": event_type,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
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
            .update({"status": new_status})
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
            .select("run_id")
            .eq("bot_id", bot_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        if getattr(response, "error", None):
            print(f"❌ Failed to fetch latest run_id: {getattr(response, 'error', 'Unknown error')}")
            return None
        return response.data[0]["run_id"] if response.data else None
    except Exception as e:
        print(f"❌ Exception while fetching latest run_id: {e}")
        return None


