from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from app.supabase_client import supabase
from app.utils.crypto import encrypt
from app.utils.auth import get_current_user_id
from datetime import datetime

router = APIRouter()

class ExchangeKeyPayload(BaseModel):
    exchange: str
    api_key_encrypted: str
    api_secret_encrypted: str

@router.get("/")
def health():
    return {"message": "Exchange Keys Endpoint Active"}

@router.post("/")
def store_exchange_keys(
    payload: ExchangeKeyPayload,
    user_id: str = Depends(get_current_user_id),
    authorization: str = Header(...)
):
    print("🔥 Received POST /exchange-keys with:", payload)
    print("👤 User ID from token:", user_id)

    try:
        encrypted_key = encrypt(payload.api_key_encrypted)
        encrypted_secret = encrypt(payload.api_secret_encrypted)

        insert_payload = {
            "user_id": user_id,
            "exchange": payload.exchange.lower(),
            "api_key_encrypted": encrypted_key,
            "api_secret_encrypted": encrypted_secret,
            "created_at": datetime.utcnow().isoformat()
        }

        print("📦 Payload to Supabase:", insert_payload)

        response = supabase.table("exchange_keys").insert(insert_payload).execute()

        print("🧾 Supabase response:", response)

        if not response.data:
            raise HTTPException(status_code=500, detail="Insert failed (check RLS or schema)")

        return {"message": "Exchange keys saved successfully"}

    except Exception as e:
        print("❌ Exception while saving exchange keys:", type(e).__name__, str(e))
        raise HTTPException(status_code=500, detail="Internal server error while storing exchange keys")
