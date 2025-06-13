from typing import Tuple, List
from app.supabase_client import supabase
from app.services.exchange_client import get_mock_balance
from app.services.supabase_queries import (
    get_user_exchange_keys,
    is_bot_already_running
)

def validate_bot(bot_id: str, user_id: str) -> Tuple[bool, dict | None, List[str]]:
    errors = []

    # 1. Fetch bot config
    response = (
        supabase
        .table("bots")
        .select("*")
        .eq("bot_id", bot_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data or len(response.data) == 0:
        return False, None, [f"Bot not found or access denied (bot_id={bot_id})"]

    bot = response.data[0]

    # 2. Check if bot is already running
    if is_bot_already_running(bot_id):
        errors.append("Bot is already running in another session.")

    # 3. Bot must be inactive
    if bot["status"] != "inactive":
        errors.append("Bot must be inactive to start.")

    # 4. Required fields
    required_fields = [
        "trading_pair", "initial_amount", "order_type",
        "dca_orders", "max_dca_orders", "dca_amount_mode", "required_capital"
    ]
    for field in required_fields:
        if not bot.get(field):
            errors.append(f"Missing required field: {field}")

    # 5. Order type validation
    if bot["order_type"] == "limit" and not bot.get("limit_price"):
        errors.append("Limit price required for limit order.")

    # 6. DCA mode validation
    if bot["dca_amount_mode"] == "fixed" and not bot.get("fixed_amount"):
        errors.append("Fixed amount is required for fixed DCA mode.")
    if bot["dca_amount_mode"] == "progressive" and not bot.get("multiplier"):
        errors.append("Multiplier is required for progressive DCA mode.")

    # 7. Check if exchange keys exist
    if not bot.get("exchange"):
        errors.append("Exchange is not specified.")
    else:
        exchange_keys = get_user_exchange_keys(user_id, bot["exchange"])
        if not exchange_keys:
            errors.append(f"No exchange keys connected for exchange: {bot['exchange']}")
    
    # 8. Soft capital check: warn if balance < required_capital
    if exchange_keys:
        balance = get_mock_balance(bot["exchange"], exchange_keys)
        if balance < bot["required_capital"]:
            errors.append(f"⚠️ Available balance (${balance}) is less than required capital (${bot['required_capital']}). Bot can still start, but may fail to place orders.")

    return len(errors) == 0, bot, errors
