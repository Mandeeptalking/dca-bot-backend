# place_initial_order.py
from app.services.exchange_client import get_exchange_client
from app.supabase_client import supabase
from datetime import datetime

def place_initial_order(bot: dict, keys: dict) -> dict:
    exchange = bot["exchange"]
    symbol = bot["trading_pair"]
    amount = bot["initial_amount"]
    order_type = bot["order_type"]
    
    # Handle both standard and conditional order types
    if order_type in ["conditional_market", "market"]:
        processed_order_type = "market"
    elif order_type in ["conditional_limit", "limit"]:
        processed_order_type = "limit"
    else:
        raise ValueError(f"Unsupported order type: '{order_type}'")
    
    # Handle limit price validation
    limit_price = bot.get("limit_price")
    try:
        # Convert to float if it exists
        limit_price = float(limit_price) if limit_price is not None else None
    except (TypeError, ValueError):
        limit_price = None

    client = get_exchange_client(exchange, keys["api_key"], keys["api_secret"])

    # Place the order based on processed order type
    if processed_order_type == "market":
        order = client.place_market_order(symbol=symbol, amount=amount, side="buy")
    
    elif processed_order_type == "limit":
        if limit_price is None or limit_price <= 0:
            raise ValueError(
                f"Limit order requires valid price. "
                f"Received: {bot.get('limit_price')} (parsed as {limit_price})"
            )
        order = client.place_limit_order(
            symbol=symbol, 
            amount=amount, 
            side="buy", 
            price=limit_price
        )
    
    # Normalize values
    price = float(order["price"])
    filled_amount = float(order["amount"])
    filled_quantity = filled_amount / price

    # Log trade to Supabase
    trade_record = {
        "bot_id": bot["bot_id"],
        "symbol": symbol,
        "price": round(price, 4),
        "amount": round(filled_amount, 4),
        "drop_pct": 0,
        "step": 0,
        "note": "Initial entry",
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("bot_trades").insert(trade_record).execute()

    return {
        "success": True,
        "order_id": order.get("order_id"),
        "price": round(price, 4),
        "amount": round(filled_amount, 4),
        "filled_quantity": round(filled_quantity, 6),
        "avg_entry_price": price,
        "last_entry_price": price,
        "timestamp": order.get("timestamp") or datetime.utcnow().isoformat()
    }