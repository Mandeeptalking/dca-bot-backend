from datetime import datetime
from app.supabase_client import supabase
from app.services.status_transition import (
    update_bot_status,
    log_bot_event,
    update_bot_run_status,
    get_latest_run_id
)

def place_initial_order(order_type, trading_pair, amount, limit_price=None):
    print(f"🛒 Placing {order_type.upper()} order for {trading_pair} - Amount: {amount}, Limit: {limit_price}")
    if order_type == "limit" and not limit_price:
        raise ValueError("Limit order requires a limit price")
    return {
        "status": "placed",
        "order_type": order_type,
        "pair": trading_pair,
        "amount": amount,
        "limit_price": limit_price,
        "placed_at": datetime.utcnow().isoformat()
    }

def run_dca_bot(bot_id: str, user_id: str):
    print(f"🚀 Running DCA bot for bot_id={bot_id}")

    # Fetch bot config
    bot_resp = supabase.table("bots").select("*").eq("bot_id", bot_id).limit(1).execute()
    if not bot_resp.data:
        return {"error": "Bot not found"}

    bot = bot_resp.data[0]

    # 1. Create a new run
    run_payload = {
        "bot_id": bot_id,
        "user_id": user_id,
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
    }

    run_resp = supabase.table("bot_runs").insert(run_payload).execute()
    if not run_resp.data:
        return {"error": "Failed to start bot run"}

    run_id = run_resp.data[0]["run_id"]
    update_bot_status(bot_id, "running")

    try:
        # 2. Place initial order if required
        trading_pair = bot.get("trading_pair")
        initial_amount = bot.get("initial_order_amount")
        order_type = bot.get("order_type", "").lower()
        limit_price = bot.get("initial_order_limit_price")

        if order_type == "market":
            order_result = place_initial_order("market", trading_pair, initial_amount)
            log_bot_event(run_id, bot_id, user_id, "initial_order_placed", order_result)

        elif order_type == "limit":
            if not limit_price:
                raise ValueError("Limit price required for limit order")
            order_result = place_initial_order("limit", trading_pair, initial_amount, limit_price)
            log_bot_event(run_id, bot_id, user_id, "initial_order_placed", order_result)

        elif order_type in ["conditional_market", "conditional_limit"]:
            print(f"⏳ Waiting for webhook to trigger {order_type.upper().replace('_', ' ')}")
            log_bot_event(run_id, bot_id, user_id, "waiting_for_condition", {
                "order_type": order_type
            })
            update_bot_run_status(run_id, "waiting")
            return {"status": "waiting", "reason": order_type}

        else:
            raise ValueError(f"Invalid order type: {order_type}")

        # TODO: Continue DCA logic here later

        update_bot_run_status(run_id, "completed")
        update_bot_status(bot_id, "completed")

        return {"status": "completed", "initial_order": order_result}

    except Exception as e:
        print(f"❌ Bot execution failed: {e}")
        update_bot_run_status(run_id, "failed")
        update_bot_status(bot_id, "error")
        log_bot_event(run_id, bot_id, user_id, "error", {"message": str(e)})
        return {"error": str(e)}
