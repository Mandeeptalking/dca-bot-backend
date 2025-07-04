from datetime import datetime, timezone
from typing import cast, Any, Optional
from typing import Optional
from app.supabase_client import supabase
from app.services.status_transition import (
    update_bot_status,
    log_bot_event,
    update_bot_run_status,
    get_latest_run_id
)
from app.services.place_initial_order import place_initial_order
from app.services.fetch_and_validate import fetch_and_validate_bot
from app.services.calculate_dca_levels import calculate_dca_levels
from app.services.calculate_take_profit import calculate_take_profit_levels
from app.services.calculate_stop_pause import calculate_stop_pause_levels
from app.services.log_bot_plan import log_bot_plan


def run_dca_bot(bot_id: str, user_id: str):
    print(f"🚀 Running DCA bot for bot_id={bot_id}")
    run_id: Optional[str] = None

    try:
        # Step 1: Fetch bot config and exchange keys
        bot, exchange_keys = fetch_and_validate_bot(bot_id, user_id)

        # Step 2: Insert new run
        run_payload = {
            "bot_id": bot_id,
            "user_id": user_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }
        run_resp = supabase.table("bot_runs").insert(run_payload).execute()
        if not run_resp.data:
            raise ValueError("❌ Failed to insert new run into bot_runs table")

        run_id = run_resp.data[0].get("run_id")
        if not run_id:
            raise ValueError("❌ Missing run_id in bot_runs insert response")

        update_bot_status(bot_id, "running")
        update_bot_run_status(run_id, "running")

        trading_pair = bot.get("trading_pair")
        order_type_raw = bot.get("order_type")
        order_type = str(order_type_raw).strip().replace(" ", "_").lower() if order_type_raw else ""
        limit_price = bot.get("limit_price")

        valid_order_types = ["market", "limit", "conditional_market", "conditional_limit"]
        if order_type not in valid_order_types:
            raise ValueError(f"Invalid order type: '{order_type_raw}' (normalized: '{order_type}')")

        if order_type in ["market", "limit"]:
            if order_type == "limit" and not limit_price:
                raise ValueError("Limit price required for limit order")

            # Step 3: Place initial order
            order_result = place_initial_order(bot, exchange_keys)

            log_bot_event(run_id, bot_id, user_id, "initial_order_placed", order_result)

            avg_entry_raw = order_result.get("avg_entry_price")
            last_entry_raw = order_result.get("last_entry_price")

            if avg_entry_raw is None or last_entry_raw is None:
                raise ValueError("Missing avg_entry_price or last_entry_price in order_result")

            avg_entry = float(avg_entry_raw)
            last_entry = float(last_entry_raw)

            # Step 4: Calculate full logic levels
            dca_levels = calculate_dca_levels(bot, last_entry)
            tp_levels = calculate_take_profit_levels(bot, avg_entry)
            stop_pause_levels = calculate_stop_pause_levels(bot, avg_entry, last_entry)

            # Step 5: Log plan
            log_bot_plan(bot_id, trading_pair, dca_levels, tp_levels, stop_pause_levels)

            return {
                "status": "running",
                "run_id": run_id,
                "initial_order": order_result
            }

        elif order_type in ["conditional_market", "conditional_limit"]:
            print(f"⏳ Waiting for webhook to trigger {order_type.upper().replace('_', ' ')} order")
            log_bot_event(run_id, bot_id, user_id, "waiting_for_condition", {
                "order_type": order_type
            })
            update_bot_run_status(run_id, "waiting")
            return {
                "status": "waiting",
                "reason": order_type,
                "run_id": run_id
            }

    except Exception as e:
        print(f"❌ Bot execution failed: {e}")
        if run_id:
            update_bot_run_status(run_id, "failed")
            update_bot_status(bot_id, "error")
            log_bot_event(run_id, bot_id, user_id, "error", {"message": str(e)})
        return {"error": str(e)}
    
from app.services.fetch_and_validate import fetch_and_validate_bot

def trigger_bot_condition(bot_id: str, user_id: str, run_id: Optional[str] = None):
    now_utc = datetime.now(timezone.utc).isoformat()
    print(f"🚀 Triggering entry condition for bot_id: {bot_id}, user_id: {user_id}, run_id: {run_id}")

    # ✅ Use same logic as non-webhook bot to fetch bot and decrypted keys
    try:
        bot, keys = fetch_and_validate_bot(bot_id, user_id, allow_running=True)
    except Exception as e:
        print(f"❌ Failed to fetch bot or exchange keys: {e}")
        return {"error": str(e)}

    # ✅ Mark entry condition as triggered
    condition_update = supabase.table("bot_conditions").update({
        "status": "triggered",
        "triggered_at": now_utc,
        "updated_at": now_utc
    }).match({
        "bot_id": bot_id,
        "type": "entry",
        "status": "waiting"
    }).execute()

    if getattr(condition_update, "error", None):
        print(f"❌ Failed to update bot_conditions: {condition_update.error}")
    else:
        print(f"✅ Updated {len(condition_update.data)} condition(s) to status=triggered")

    # ✅ Resolve run_id if not provided
    if not run_id:
        run_resp = (
            supabase.table("bot_runs")
            .select("run_id")
            .eq("bot_id", bot_id)
            .eq("user_id", user_id)
            .eq("status", "waiting")
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        if getattr(run_resp, "error", None):
            print(f"❌ Error fetching bot_runs: {run_resp.error}")
        elif run_resp.data:
            run_id = run_resp.data[0]["run_id"]
            print(f"🔁 Resolved run_id from waiting: {run_id}")
        else:
            print("⚠️ No waiting bot_run found for this bot")

    # ✅ Update bot_run and bot status
    if run_id:
        update_bot_run_status(run_id, "running")
        log_bot_event(run_id, bot_id, user_id, "entry_triggered", {
            "message": "Entry condition triggered by webhook"
        })

    if bot.get("status") != "running":
        update_bot_status(bot_id, "running")

    # ✅ Place the initial order
    order_result = place_initial_order(bot, keys)
    print("✅ Initial order placement complete")

    # ✅ Post-order logic
    avg_entry_raw = order_result.get("avg_entry_price")
    last_entry_raw = order_result.get("last_entry_price")

    if avg_entry_raw is None or last_entry_raw is None:
        raise ValueError("Missing avg_entry_price or last_entry_price in order_result")

    avg_entry = float(avg_entry_raw)
    last_entry = float(last_entry_raw)

    # ✅ Calculate logic levels
    dca_levels = calculate_dca_levels(bot, last_entry)
    tp_levels = calculate_take_profit_levels(bot, avg_entry)
    stop_pause_levels = calculate_stop_pause_levels(bot, avg_entry, last_entry)

    # ✅ Log plan
    trading_pair = bot.get("trading_pair") or "UNKNOWN"
    log_bot_plan(bot_id, trading_pair, dca_levels, tp_levels, stop_pause_levels)

    return {
        "status": "running",
        "run_id": run_id,
        "initial_order": order_result,
    }
