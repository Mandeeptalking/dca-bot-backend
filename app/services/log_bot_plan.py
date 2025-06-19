# app/services/log_bot_plan.py

from datetime import datetime
from app.supabase_client import supabase


def log_bot_plan(bot_id: str, symbol: str, dca_levels: list, tp_levels: list, stop_pause: dict):
    """
    Step 5: Log initial trade plan to Supabase.
    Stores DCA orders, take profit targets, and stop/pause conditions.
    """
    trade_entries = []

    now = datetime.utcnow().isoformat()

    # DCA Levels
    for dca in dca_levels:
        trade_entries.append({
            "bot_id": bot_id,
            "symbol": symbol,
            "price": dca["trigger_price"],
            "amount": dca["amount"],
            "drop_pct": dca["drop_pct"],
            "step": dca["step"],
            "note": "DCA Order",
            "created_at": now
        })

    # Take Profit Levels
    for tp in tp_levels:
        trade_entries.append({
            "bot_id": bot_id,
            "symbol": symbol,
            "price": tp["trigger_price"],
            "amount": tp["position_size"],
            "drop_pct": tp["trigger_pct"],
            "step": tp["step"],
            "note": "Take Profit",
            "created_at": now
        })

    # Stop Conditions
    for stop in stop_pause.get("stop", []):
        trade_entries.append({
            "bot_id": bot_id,
            "symbol": symbol,
            "price": stop["trigger_price"],
            "amount": 0,
            "drop_pct": stop["drop_pct"],
            "step": 0,
            "note": f"STOP: {stop['type']}",
            "created_at": now
        })

    # Pause Conditions
    for pause in stop_pause.get("pause", []):
        trade_entries.append({
            "bot_id": bot_id,
            "symbol": symbol,
            "price": pause["trigger_price"],
            "amount": 0,
            "drop_pct": pause["drop_pct"],
            "step": 0,
            "note": f"PAUSE: {pause['type']}",
            "created_at": now
        })

    # Insert all to Supabase
    if not trade_entries:
        raise Exception("No trade entries to insert.")

    try:
        response = supabase.table("bot_trades").insert(trade_entries).execute()

        # Safely check for Supabase errors
        error = getattr(response, "error", None)
        if error:
            raise Exception(f"Supabase insert error: {error}")

        return response

    except Exception as e:
        raise Exception(f"❌ Failed to log bot plan: {str(e)}")
