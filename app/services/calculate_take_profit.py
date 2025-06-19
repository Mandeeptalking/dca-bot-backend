# calculate_take_profit.py

def calculate_take_profit_levels(bot: dict, avg_entry_price: float) -> list:
    """
    Step 4: Convert take profit targets (percentage) into absolute price levels.
    Returns a list of dicts with price target, size %, and step.
    """
    tp_config = bot.get("take_profit", {})
    targets = tp_config.get("targets", [])

    if not targets:
        return []

    levels = []
    for i, tp in enumerate(targets):
        trigger_pct = tp.get("triggerPrice")
        position_size = tp.get("positionSize")

        if trigger_pct is None or position_size is None:
            continue

        trigger_price = round(avg_entry_price * (1 + trigger_pct / 100), 4)

        levels.append({
            "step": i + 1,
            "trigger_pct": trigger_pct,
            "trigger_price": trigger_price,
            "position_size": position_size
        })

    return levels
