# preflight.py

from typing import Tuple, List
from app.supabase_client import supabase
from app.services.supabase_queries import get_user_exchange_keys, is_bot_already_running
from app.services.exchange_client import get_mock_balance


def validate_bot(bot_id: str, user_id: str) -> Tuple[bool, dict | None, List[str]]:
    """
    Validates the bot before execution.
    Returns: (is_valid, bot_config or None, list of error/warning messages)
    """
    errors = []
    warnings = []

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

    if not response.data:
        return False, None, ["Bot not found or access denied."]

    bot = response.data[0]

    # 2. Check if bot is already running — only if status is not 'stopped'
    if bot["status"] != "stopped" and is_bot_already_running(bot_id):
        errors.append("Bot is already running in another session.")

    # 3. Bot must be inactive or stopped
    print(f"🧪 Bot status during preflight: {bot['status']}")
    if bot["status"] not in ["inactive", "stopped"]:
        errors.append("Bot must be inactive or stopped to start.")

    # 4. Required fields check
    required_fields = [
        "trading_pair", "initial_amount", "order_type",
        "dca_orders", "max_dca_orders", "dca_amount_mode",
        "required_capital", "take_profit"
    ]
    for field in required_fields:
        if not bot.get(field):
            errors.append(f"Missing required field: {field}")

    # 5. Order type validation
    if bot["order_type"] == "limit" and not bot.get("limit_price"):
        errors.append("Limit price is required for limit order type.")

    # 6. DCA mode validation
    if bot["dca_amount_mode"] == "fixed" and not bot.get("fixed_amount"):
        errors.append("Fixed amount is required for fixed DCA mode.")
    if bot["dca_amount_mode"] == "progressive" and not bot.get("multiplier"):
        errors.append("Multiplier is required for progressive DCA mode.")

    # 7. Check exchange connection
    if not bot.get("exchange"):
        errors.append("Exchange is not specified.")
    else:
        exchange_keys = get_user_exchange_keys(user_id, bot["exchange"])
        if not exchange_keys:
            errors.append("No exchange keys connected for this user and exchange.")

    # 8. Check balance if keys are valid
    if not errors and exchange_keys:
        balance = get_mock_balance(bot["exchange"], exchange_keys)

        if balance < bot["initial_amount"]:
            errors.append("❌ Insufficient balance to place initial order.")
        elif balance < bot["required_capital"]:
            warnings.append("⚠️ Balance is below required capital. Bot will start but may not complete all DCA steps.")

    # 9. Check take profit conditions
    take_profit = bot.get("take_profit", {})
    if not take_profit.get("targets"):
        errors.append("At least one take profit target is required.")

    return (len(errors) == 0), bot, errors + warnings
