from app.supabase_client import supabase

# ✅ Fetch connected exchange keys for a user and exchange
def get_user_exchange_keys(user_id: str, exchange: str):
    response = (
        supabase
        .table("exchange_keys")
        .select("*")
        .eq("user_id", user_id)
        .eq("exchange", exchange)
        .limit(1)
        .execute()
    )
    if not response.data or len(response.data) == 0:
        return None
    return response.data[0]

# ✅ Check if the bot is already running (used during preflight)
def is_bot_already_running(bot_id: str) -> bool:
    response = (
        supabase
        .table("bot_runs")
        .select("run_id")
        .eq("bot_id", bot_id)
        .in_("status", ["running", "paused"])  # ✅ Include only active statuses
        .limit(1)
        .execute()
    )
    return bool(response.data and len(response.data) > 0)

