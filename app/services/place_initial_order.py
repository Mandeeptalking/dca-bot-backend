# place_initial_order.py

from app.services.exchange_client import get_exchange_client
from app.supabase_client import supabase
from datetime import datetime

def place_initial_order(bot: dict, keys: dict) -> dict:
    """
    Step 2: Place the initial market or limit order for the DCA bot.
    Returns: dict with order details (price, quantity, etc.)
    """
    exchange = bot["exchange"]
    symbol = bot["trading_pair"]
    amount = bot["initial_amount"]
    order_type = bot["order_type"]
    limit_price = bot.get("limit_price")

    client = get_exchange_client(exchange, keys["api_key"], keys["api_secret"])

    # Place the order
    if order_type == "market":
        order = client.place_market_order(symbol=symbol, amount=amount, side="buy")
    elif order_type == "limit" and limit_price:
        order = client.place_limit_order(symbol=symbol, amount=amount, side="buy", price=limit_price)
    else:
        raise ValueError("Invalid order type or missing limit price")

    # Log trade to Supabase
    trade_record = {
        "bot_id": bot["bot_id"],
        "symbol": symbol,
        "price": round(order["price"], 4),
        "amount": round(order["amount"], 4),
        "drop_pct": 0,
        "step": 0,  # initial order is step 0
        "note": "Initial entry",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("bot_trades").insert(trade_record).execute()

    return order
