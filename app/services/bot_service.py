# app/services/bot_service.py

from app.supabase_client import supabase

def get_all_bots():
    response = supabase.table("bots").select("*").limit(10).execute()
    return response.data
