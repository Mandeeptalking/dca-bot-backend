from app.supabase_client import supabase
import datetime
from typing import List, Dict, Any, Optional

# Constants
STATUS_WAITING = "waiting"
STATUS_TRIGGERED = "triggered"
STATUS_EXPIRED = "expired"
STATUS_COMPLETED = "completed"
STATUS_SKIPPED = "skipped"

def get_active_bot_conditions(bot_id: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    # Base query to get active conditions
    query = supabase.table("bot_conditions").select("*").in_("status", [STATUS_WAITING, STATUS_TRIGGERED])

    # Handle user_id filtering through bots table
    if user_id:
        # Get bot IDs associated with this user - CORRECTED COLUMN NAME
        bot_resp = supabase.table("bots").select("bot_id").eq("user_id", user_id).execute()
        user_bot_ids = [bot["bot_id"] for bot in bot_resp.data]  # Changed to bot_id
        
        if not user_bot_ids:
            return []  # User has no bots
        
        # Apply bot ID filter
        query = query.in_("bot_id", user_bot_ids)
    
    # Apply direct bot_id filter if provided
    if bot_id:
        query = query.eq("bot_id", bot_id)

    resp = query.execute()
    return resp.data

def is_condition_expired(condition: Dict[str, Any]) -> bool:
    if condition["status"] != STATUS_TRIGGERED:
        return False
    if not condition.get("triggered_at") or not condition.get("valid_for_secs"):
        return False
    triggered_at = datetime.datetime.fromisoformat(condition["triggered_at"])
    expires_at = triggered_at + datetime.timedelta(seconds=condition["valid_for_secs"])
    return datetime.datetime.utcnow() > expires_at

def evaluate_condition_logic(conditions: List[Dict[str, Any]], operator: Optional[str]) -> bool:
    """Evaluate condition group logic (AND/OR)"""
    operator = (operator or "and").lower()
    flags = [cond['status'] == STATUS_TRIGGERED for cond in conditions]
    return all(flags) if operator == "and" else any(flags)

def reset_expired_conditions():
    """Reset expired conditions to expired status"""
    conditions = get_active_bot_conditions()
    for condition in conditions:
        if is_condition_expired(condition):
            supabase.table("bot_conditions") \
                .update({"status": STATUS_EXPIRED}) \
                .eq("id", condition["id"]) \
                .execute()

def evaluate_condition_groups(bot_id: Optional[str] = None, user_id: Optional[str] = None):
    """Evaluate all condition groups for a bot/user"""
    all_conditions = get_active_bot_conditions(bot_id, user_id)
    grouped: Dict[int, List[Dict[str, Any]]] = {}

    for cond in all_conditions:
        group_num = cond["group_num"]
        grouped.setdefault(group_num, []).append(cond)

    for group_num, conditions in grouped.items():
        operator = conditions[0].get("logic_operator") or "and"
        condition_type = conditions[0].get("type")

        # Skip group if any condition expired
        if any(is_condition_expired(c) for c in conditions):
            for c in conditions:
                if c["status"] == STATUS_TRIGGERED:
                    supabase.table("bot_conditions").update({"status": STATUS_EXPIRED}).eq("id", c["id"]).execute()
            continue

if __name__ == "__main__":
    reset_expired_conditions()
    evaluate_condition_groups()