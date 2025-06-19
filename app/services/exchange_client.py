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

def get_mock_balance(exchange: str, keys: dict) -> float:
    # Replace this mock logic with actual API call later
    print(f"[MOCK BALANCE] Checking balance for {exchange} using {keys}")
    return 10000.00  # assume sufficient balance for now

# -----------------------------------------------
# ✅ Exchange client factory
# -----------------------------------------------

class MockExchangeClient:
    def place_market_order(self, symbol: str, amount: float, side: str):
        print(f"[MOCK] Market {side} order for {amount} of {symbol}")
        return {"price": 1.0, "amount": amount}  # mock data

    def place_limit_order(self, symbol: str, amount: float, side: str, price: float):
        print(f"[MOCK] Limit {side} order for {amount} of {symbol} at {price}")
        return {"price": price, "amount": amount}  # mock data


def get_exchange_client(exchange: str, api_key: str, api_secret: str):
    if exchange.lower() == "binance":
        # TODO: Replace with actual BinanceClient when ready
        return MockExchangeClient()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange}")
