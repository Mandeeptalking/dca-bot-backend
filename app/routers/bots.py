from fastapi import APIRouter, HTTPException
from app.supabase_client import supabase

router = APIRouter()

@router.get("/{bot_id}")
def get_bot(bot_id: str):
    response = (
        supabase
        .table("bots")
        .select("*")
        .eq("bot_id", bot_id)  # ✅ updated from 'id'
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Bot not found")

    return response.data
