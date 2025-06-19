# app/services/bot_service.py

from app.supabase_client import supabase
from fastapi import HTTPException
from typing import Optional


def get_all_bots(limit: int = 20):
    try:
        response = supabase.table("bots").select("*").limit(limit).execute()
        if response.data:
            return response.data
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch bots: {str(e)}")


def get_user_bots(user_id: str, status: Optional[str] = None):
    try:
        query = supabase.table("bots").select("*").eq("user_id", user_id)
        if status:
            query = query.eq("status", status)
        response = query.order("created_at", desc=True).execute()
        return response.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user bots: {str(e)}")


def get_bot_by_id(bot_id: str):
    try:
        response = (
            supabase.table("bots")
            .select("*")
            .eq("bot_id", bot_id)
            .single()
            .execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Bot not found")
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bot: {str(e)}")

# app/services/bot_service.py

def delete_bot_completely(bot_id: str):
    # Step 1: Delete from dependent tables
    supabase.table("bot_runs").delete().eq("bot_id", bot_id).execute()
    supabase.table("bot_logs").delete().eq("bot_id", bot_id).execute()
    supabase.table("bot_trades").delete().eq("bot_id", bot_id).execute()

    # Step 2: Delete from bots
    supabase.table("bots").delete().eq("bot_id", bot_id).execute()

    print(f"🗑️ Deleted bot and all related records for bot_id={bot_id}")

