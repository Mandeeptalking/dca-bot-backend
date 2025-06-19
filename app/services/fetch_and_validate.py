# fetch_and_validate.py

from app.supabase_client import supabase
from app.utils.crypto import decrypt
from app.services.supabase_queries import get_user_exchange_keys
from fastapi import HTTPException

def fetch_and_validate_bot(bot_id: str, user_id: str) -> tuple:
    """
    Step 1: Fetch bot config, validate status, and fetch/decrypt exchange keys.
    Returns: (bot_config: dict, decrypted_keys: dict)
    Raises: HTTPException on validation failure
    """
    # 1. Fetch bot config
    response = (
        supabase
        .table("bots")
        .select("*")
        .eq("bot_id", bot_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Bot not found or access denied")

    bot = response.data[0]

    # 2. Ensure bot is inactive
    if bot["status"] not in ["inactive", "stopped"]:
        raise HTTPException(status_code=400, detail="Bot must be inactive or stopped to start")

    # 3. Fetch and decrypt exchange keys
    exchange_keys = get_user_exchange_keys(user_id, bot["exchange"])
    if not exchange_keys:
        raise HTTPException(status_code=400, detail="Exchange keys not found for user")

    decrypted_keys = {
        "api_key": decrypt(exchange_keys["api_key_encrypted"]),
        "api_secret": decrypt(exchange_keys["api_secret_encrypted"])
    }

    return bot, decrypted_keys
