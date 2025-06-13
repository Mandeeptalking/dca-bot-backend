from app.supabase_client import supabase

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

def is_bot_already_running(bot_id: str) -> bool:
    response = (
        supabase
        .table("bot_runs")
        .select("run_id")  # You can choose any column
        .eq("bot_id", bot_id)
        .eq("status", "running")
        .limit(1)
        .execute()
    )
    return bool(response.data and len(response.data) > 0)

