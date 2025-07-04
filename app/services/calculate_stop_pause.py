def calculate_stop_pause_levels(bot: dict, avg_entry: float, last_entry: float) -> dict:
    """
    Converts stop and pause condition percentages into trigger prices.

    Args:
        bot (dict): The bot configuration containing stop/pause settings.
        avg_entry (float): Average entry price.
        last_entry (float): Last entry price.

    Returns:
        dict: {
            "stop": [ {type, trigger_price, drop_pct}, ... ],
            "pause": [ {type, trigger_price, drop_pct}, ... ]
        }
    """
    stop_config = bot.get("stop_conditions", {})
    pause_config = bot.get("pause_conditions", {})

    def calculate_level(config: dict, key: str, base_price: float):
        if config.get(key, {}).get("enabled"):
            drop_pct = config[key].get("value")
            if drop_pct is not None:
                trigger_price = round(base_price * (1 - drop_pct / 100), 4)
                return {
                    "type": key,
                    "trigger_price": trigger_price,
                    "drop_pct": drop_pct
                }
        return None

    stop_levels = list(filter(None, [
        calculate_level(stop_config, "priceDropFromLast", last_entry),
        calculate_level(stop_config, "priceDropFromAvg", avg_entry)
    ]))

    pause_levels = list(filter(None, [
        calculate_level(pause_config, "priceDropFromLast", last_entry),
        calculate_level(pause_config, "priceDropFromAvg", avg_entry)
    ]))

    return {
        "stop": stop_levels,
        "pause": pause_levels
    }
