# calculate_stop_pause.py

def calculate_stop_pause_levels(bot: dict, avg_entry: float, last_entry: float) -> dict:
    """
    Step 4b: Convert stop and pause conditions to fixed price triggers.
    Returns a dict with lists of stop and pause triggers.
    """
    stop_config = bot.get("stop_conditions", {})
    pause_config = bot.get("pause_conditions", {})

    stop_levels = []
    pause_levels = []

    # --- STOP CONDITIONS ---
    if stop_config.get("priceDropFromLast", {}).get("enabled"):
        drop_pct = stop_config["priceDropFromLast"]["value"]
        trigger_price = round(last_entry * (1 - drop_pct / 100), 4)
        stop_levels.append({"type": "priceDropFromLast", "trigger_price": trigger_price, "drop_pct": drop_pct})

    if stop_config.get("priceDropFromAvg", {}).get("enabled"):
        drop_pct = stop_config["priceDropFromAvg"]["value"]
        trigger_price = round(avg_entry * (1 - drop_pct / 100), 4)
        stop_levels.append({"type": "priceDropFromAvg", "trigger_price": trigger_price, "drop_pct": drop_pct})

    # --- PAUSE CONDITIONS ---
    if pause_config.get("priceDropFromLast", {}).get("enabled"):
        drop_pct = pause_config["priceDropFromLast"]["value"]
        trigger_price = round(last_entry * (1 - drop_pct / 100), 4)
        pause_levels.append({"type": "priceDropFromLast", "trigger_price": trigger_price, "drop_pct": drop_pct})

    if pause_config.get("priceDropFromAvg", {}).get("enabled"):
        drop_pct = pause_config["priceDropFromAvg"]["value"]
        trigger_price = round(avg_entry * (1 - drop_pct / 100), 4)
        pause_levels.append({"type": "priceDropFromAvg", "trigger_price": trigger_price, "drop_pct": drop_pct})

    return {
        "stop": stop_levels,
        "pause": pause_levels
    }
