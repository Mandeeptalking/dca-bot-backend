from datetime import datetime, timezone
from typing import Optional, Dict, Any
from typing import cast
from app.supabase_client import supabase
from app.services.status_transition import (
    update_bot_run_status,
    update_bot_status,
    log_bot_event,
)
from app.services.place_initial_order import place_initial_order
from app.services.calculate_dca_levels import calculate_dca_levels
from app.services.calculate_take_profit import calculate_take_profit_levels
from app.services.calculate_stop_pause import calculate_stop_pause_levels
from app.services.log_bot_plan import log_bot_plan


def trigger_bot_condition(bot_id: str, user_id: str, run_id: Optional[str] = None) -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc).isoformat()

    print(f"🚀 Triggering webhook-based entry for bot_id={bot_id}, user_id={user_id}, run_id={run_id}")

    # ✅ Fetch bot config
    bot_resp = supabase.table("bots").select("*").eq("bot_id", bot_id).eq("user_id", user_id).single().execute()
    bot = getattr(bot_resp, "data", None)
    if bot is None:
        print("❌ Error fetching bot config")
        return {"error": "Failed to fetch bot config"}

    # ✅ Fetch exchange keys
    keys_resp = supabase.table("exchange_keys").select("*").eq("user_id", user_id).eq("exchange", bot["exchange"]).single().execute()
    keys = getattr(keys_resp, "data", None)
    if keys is None:
        print("❌ Error fetching exchange keys")
        return {"error": "Failed to fetch exchange keys"}

    # ✅ Update entry condition
    cond_update = supabase.table("bot_conditions").update({
        "stage": "executed",
        "triggered": True
    }).match({
        "bot_id": bot_id,
        "user_id": user_id,
        "type": "entry"
    }).execute()
    if not getattr(cond_update, "data", None):
        print("❌ Failed to update bot_conditions")
    else:
        print("✅ Entry condition marked as executed")

    # ✅ Resolve run_id if not passed
    if run_id is None:
        run_resp = (
            supabase.table("bot_runs")
            .select("run_id")
            .eq("bot_id", bot_id)
            .eq("status", "waiting")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        run_data = getattr(run_resp, "data", None)
        if not run_data:
            print("⚠️ No waiting run_id found")
            return {"error": "No waiting run_id found"}
        run_id = run_data[0]["run_id"]
        print(f"🔁 Resolved waiting run_id: {run_id}")

    # ✅ Update run + bot status
    update_bot_run_status(cast(str, run_id), "running")
    update_bot_status(bot_id, "running")

    # ✅ Mark run stage
    supabase.table("bot_runs").update({
        "stage": "entry_executed",
        "updated_at": now_utc
    }).eq("run_id", run_id).execute()

    log_bot_event(str(run_id), bot_id, user_id, "entry_triggered", {
        "message": "Webhook triggered entry execution"
    })

    # ✅ Place the initial order
    order_result = place_initial_order(bot, keys)
    if not order_result:
        return {"error": "Order placement failed"}

    avg_entry_raw = order_result.get("avg_entry_price")
    last_entry_raw = order_result.get("last_entry_price")

    if avg_entry_raw is None or last_entry_raw is None:
        return {"error": "Missing price in order result"}

    avg_entry = float(avg_entry_raw)
    last_entry = float(last_entry_raw)

    # ✅ Calculate logic
    dca_levels = calculate_dca_levels(bot, last_entry)
    tp_levels = calculate_take_profit_levels(bot, avg_entry)
    stop_levels = calculate_stop_pause_levels(bot, avg_entry, last_entry)

    # ✅ Log full plan
    trading_pair = bot.get("trading_pair") or "UNKNOWN"
    log_bot_plan(bot_id, trading_pair, dca_levels, tp_levels, stop_levels)

    return {
        "status": "running",
        "run_id": run_id,
        "initial_order": order_result
    }
