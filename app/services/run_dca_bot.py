# run_dca_bot.py

from app.services.fetch_and_validate import fetch_and_validate_bot
from app.services.place_initial_order import place_initial_order
from app.services.calculate_dca_levels import calculate_dca_levels
from app.services.calculate_take_profit import calculate_take_profit_levels
from app.services.calculate_stop_pause import calculate_stop_pause_levels
from app.services.log_bot_plan import log_bot_plan
from app.services.finalize_bot_run import finalize_bot_run


def run_dca_bot(bot_id: str, user_id: str):
    """
    Master function to run the full DCA bot setup.
    """
    print(f"⚙️ Starting run_dca_bot for bot_id={bot_id}, user_id={user_id}")

    # Step 1: Fetch + Validate
    print("✅ Step 1: Fetching and validating bot...")
    bot, keys = fetch_and_validate_bot(bot_id, user_id)
    print("✔️ Bot fetched and validated")

    # Step 2: Place Initial Order
    print("✅ Step 2: Placing initial order...")
    initial_order = place_initial_order(bot, keys)
    entry_price = initial_order["price"]
    print(f"✔️ Initial order placed at price: {entry_price}")

    # Step 3: Calculate DCA levels
    print("✅ Step 3: Calculating DCA levels...")
    dca_levels = calculate_dca_levels(bot, entry_price)
    print(f"✔️ DCA levels calculated: {len(dca_levels)} levels")

    # Step 4: Calculate Take Profit levels
    print("✅ Step 4: Calculating take profit levels...")
    tp_levels = calculate_take_profit_levels(bot, avg_entry_price=entry_price)
    print(f"✔️ Take profit levels calculated: {len(tp_levels)} targets")

    # Step 4b: Calculate Stop and Pause conditions
    print("✅ Step 4b: Calculating stop and pause conditions...")
    stop_pause = calculate_stop_pause_levels(bot, avg_entry=entry_price, last_entry=entry_price)
    print(f"✔️ Stop/Pause calculated → Stop: {len(stop_pause.get('stop', []))}, Pause: {len(stop_pause.get('pause', []))}")

    # Step 5: Log full trade plan
    try:
        print("✅ Step 5: Logging trade plan to Supabase...")
        log_bot_plan(
            bot_id=bot_id,
            symbol=bot["trading_pair"],
            dca_levels=dca_levels,
            tp_levels=tp_levels,
            stop_pause=stop_pause
        )
        print("📦 Supabase insert assumed successful (no error returned)")
        print("✔️ Trade plan logged")
    except Exception as e:
        print(f"❌ Failed in log_bot_plan: {e}")
        raise

    # Step 6: Finalize and update bot status
    try:
        print("✅ Step 6: Finalizing and updating bot status...")
        run_id = finalize_bot_run(bot)
        print(f"✔️ Bot run finalized with run_id: {run_id}")
    except Exception as e:
        print(f"❌ Failed in finalize_bot_run: {e}")
        raise

    return {
        "status": "started",
        "bot_id": bot_id,
        "run_id": run_id,  # ✅ Consistent naming
        "initial_price": entry_price,
        "dca_steps": len(dca_levels),
        "tp_targets": len(tp_levels),
        "stop_conditions": len(stop_pause.get("stop", [])),
        "pause_conditions": len(stop_pause.get("pause", []))
    }
