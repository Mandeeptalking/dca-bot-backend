def calculate_take_profit_levels(bot: dict, avg_entry_price: float) -> list:
    """
    Convert take profit targets into absolute price levels.

    Each take profit step includes:
    - trigger_price: calculated from avg_entry_price * (1 + trigger_pct / 100)
    - trigger_pct: the % gain from entry
    - position_size: % of position to exit
    - step: order of execution
    """
    tp_config = bot.get("take_profit", {})
    targets = tp_config.get("targets", [])

    if not targets:
        return []

    levels = []
    for i, tp in enumerate(targets):
        # Normalize keys from frontend if needed
        trigger_pct = tp.get("triggerPrice") or tp.get("trigger_pct")
        position_size = tp.get("positionSize") or tp.get("position_size")

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
