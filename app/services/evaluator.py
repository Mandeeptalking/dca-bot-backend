from datetime import datetime, timezone
from collections import defaultdict
from app.supabase_client import supabase

# 🔧 Log bot event into Supabase
def log_bot_event(bot_id: str, event: str, metadata: dict = {}):
    supabase.table("bot_logs").insert({
        "bot_id": bot_id,
        "event": event,
        "metadata": metadata,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }).execute()

# 🔧 Bot trigger stub (for later integration)
def trigger_bot_action(bot_id: str):
    print(f"🚀 EXECUTING BOT {bot_id}")
    # TODO: Replace this with actual bot runner trigger (e.g. run_dca_bot)

# 🔍 Evaluate condition groups per bot
def evaluate_condition_groups():
    print("🔁 Evaluating bot conditions...")

    # Step 1: Fetch all triggered conditions that haven't expired yet
    resp = supabase.table("bot_conditions").select("*").eq("status", "triggered").execute()
    conditions = resp.data or []

    now = datetime.now(timezone.utc)

    # Group conditions by bot_id
    bots_conditions = defaultdict(list)
    for cond in conditions:
        # Calculate how long since this condition was triggered
        triggered_at = datetime.fromisoformat(cond["triggered_at"].replace("Z", "+00:00"))
        elapsed = (now - triggered_at).total_seconds()

        # Expire stale conditions
        if elapsed > cond["validity_secs"]:
            print(f"⏱️ Expiring stale condition {cond['id']} (bot {cond['bot_id']})")
            supabase.table("bot_conditions").update({
                "status": "expired"
            }).eq("id", cond["id"]).execute()

            log_bot_event(cond["bot_id"], "condition_expired", {
                "condition_id": cond["id"],
                "reason": f"Expired after {cond['validity_secs']}s"
            })
            continue

        # Add still-valid condition to that bot's group
        bots_conditions[cond["bot_id"]].append(cond)

    # Step 2: Evaluate grouped logic
    for bot_id, conds in bots_conditions.items():
        print(f"📊 Evaluating bot {bot_id} with {len(conds)} valid triggered conditions")

        # Group conditions by group_num
        grouped = defaultdict(list)
        for cond in conds:
            grouped[cond["group_num"]].append(cond)

        # Evaluate each group
        group_results = []
        for group_num, group_conds in grouped.items():
            logic = group_conds[0].get("logic", "AND").upper()
            result_flags = []

            for cond in group_conds:
                # Already checked validity above
                if cond["status"] == "triggered" and cond.get("triggered_at"):
                    result_flags.append(True)
                else:
                    result_flags.append(False)

            group_pass = all(result_flags) if logic == "AND" else any(result_flags)
            print(f"🔍 Group {group_num} evaluated as {group_pass} with logic '{logic}'")
            group_results.append(group_pass)

        # Final trigger decision: all groups must be True
        if all(group_results):
            print(f"✅ All condition groups passed — triggering bot {bot_id}")
            trigger_bot_action(bot_id)
            log_bot_event(bot_id, "executed", {
                "group_results": group_results,
                "triggered_condition_ids": [c["id"] for c in conds]
            })
        else:
            print(f"🟡 Not all groups satisfied — bot {bot_id} is waiting")
            log_bot_event(bot_id, "waiting", {
                "group_results": group_results
            })
