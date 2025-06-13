# app/services/exchange_client.py

from datetime import datetime
from fastapi import HTTPException

from app.supabase_client import supabase
from app.utils.crypto import encrypt


def save_exchange_keys(user_id: str, exchange: str, api_key: str, api_secret: str):
    try:
        encrypted_key = encrypt(api_key)
        encrypted_secret = encrypt(api_secret)

        response = (
            supabase
            .table("exchange_keys")
            .insert({
                "user_id": user_id,
                "exchange": exchange.lower(),
                "api_key_encrypted": encrypted_key,
                "api_secret_encrypted": encrypted_secret,
                "created_at": datetime.utcnow().isoformat()
            })
            .execute()
        )

        if response.error:  # type: ignore[attr-defined]
            raise Exception(response.error)  # type: ignore[attr-defined]

        return True

    except Exception as e:
        print("Error saving exchange keys:", e)
        raise HTTPException(status_code=500, detail="Failed to store exchange keys")
