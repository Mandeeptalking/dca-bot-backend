# calculate_dca_levels.py

def calculate_dca_levels(bot: dict, entry_price: float) -> list:
    """
    Step 3: Calculate DCA trigger prices and amounts based on the selected DCA condition.
    Returns a list of dicts with drop %, trigger price, amount, and step.
    """
    levels = []

    condition = bot["dca_condition"]

    # Determine number of DCA steps
    max_steps = bot["max_dca_orders"] - bot["dca_orders"]
    if max_steps <= 0:
        return []

    progressive = bot.get("progressive_drops", {})
    progressive_enabled = progressive.get("enabled", False)
    progressive_multiplier = progressive.get("multiplier", 1)

    # Starting values
    current_price = entry_price
    current_amount = bot["initial_amount"]

    for step in range(1, max_steps + 1):
        if condition == "lossAmount":
            # Convert loss amount to price drop (approximation)
            capital = bot["initial_amount"]
            loss_amount = bot["loss_amount"]
            total_qty = capital / entry_price
            trigger_price = entry_price - (loss_amount / total_qty)
            current_drop_pct = round((entry_price - trigger_price) / entry_price * 100, 2)
        elif condition == "lastEntry":
            current_drop_pct = bot["last_entry_drop"]
            trigger_price = round(current_price * (1 - current_drop_pct / 100), 4)
        elif condition == "averageEntry":
            current_drop_pct = bot["average_entry_drop"]
            trigger_price = round(current_price * (1 - current_drop_pct / 100), 4)
        elif condition == "lossPercent":
            current_drop_pct = bot["loss_percentage"]
            trigger_price = round(current_price * (1 - current_drop_pct / 100), 4)
        else:
            raise ValueError("Unsupported DCA condition")

        # Determine amount for this step
        if bot["dca_amount_mode"] == "fixed":
            amount = bot["fixed_amount"]
        elif bot["dca_amount_mode"] == "multiplier":
            amount = round(current_amount * bot["multiplier"], 2)
            current_amount = amount  # for next iteration
        else:
            raise ValueError("Invalid DCA amount mode")

        levels.append({
            "step": step,
            "drop_pct": round(current_drop_pct, 2),
            "trigger_price": trigger_price,
            "amount": amount
        })

        current_price = trigger_price

        if progressive_enabled and condition != "lossAmount":
            current_drop_pct *= progressive_multiplier

    return levels
