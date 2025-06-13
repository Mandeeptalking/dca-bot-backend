from fastapi import APIRouter, HTTPException
from app.supabase_client import supabase

router = APIRouter()

@router.get("/{bot_id}")
def get_bot(bot_id: str):
    try:
        response = (
            supabase
            .table("bots")
            .select("*")
            .eq("bot_id", bot_id)  # ✅ updated from 'id'
            .limit(1)
            .execute()
        )

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Bot not found")

        return response.data[0]

    except Exception as e:
        print("ERROR fetching bot:", e)
        raise HTTPException(status_code=500, detail="Supabase fetch error: " + str(e))
