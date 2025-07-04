# app/services/place_dca_orders.py

from datetime import datetime
from app.services.exchange_client import get_exchange_client
from app.supabase_client import supabase


def place_dca_orders(dca_levels: list, exchange: str, keys: dict, symbol: str):
    """
    Step 4: Place all calculated DCA limit orders on the user's exchange
    and optionally log them to Supabase.
    """
    client = get_exchange_client(exchange, keys["api_key"], keys["api_secret"])
    placed_orders = []

    for dca in dca_levels:
        try:
            order = client.place_limit_order(
                symbol=symbol,
                amount=dca["amount"],
                side="buy",
                price=dca["trigger_price"]
            )

            order_record = {
                "step": dca["step"],
                "price": order["price"],
                "amount": order["amount"],
                "quantity": order.get("quantity"),
                "trigger_price": dca["trigger_price"]
            }

            placed_orders.append(order_record)

            # Optional: log to Supabase
            if "bot_id" in dca:
                supabase.table("bot_trades").insert({
                    "bot_id": dca["bot_id"],
                    "symbol": symbol,
                    "price": round(order["price"], 4),
                    "amount": round(order["amount"], 4),
                    "quantity": round(order.get("quantity", 0), 4),
                    "drop_pct": dca.get("drop_pct", 0),
                    "step": dca["step"],
                    "note": "DCA limit order",
                    "created_at": datetime.utcnow().isoformat()
                }).execute()

        except Exception as e:
            print(f"[ERROR] Failed to place DCA order for step {dca['step']}: {e}")

    return placed_orders
