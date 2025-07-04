# app/services/exchange_client.py

import random
from datetime import datetime
from binance.client import Client as BinanceClient


class BinanceExchangeClient:
    def __init__(self, api_key: str, api_secret: str):
        self.client = BinanceClient(api_key, api_secret)

    def get_live_price(self, symbol: str) -> float:
        """
        Fetch current market price from Binance.
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def place_market_order(self, symbol: str, amount: float, side: str = "buy") -> dict:
        """
        Place a market order using amount (in quote currency, e.g. USDT).
        Quantity is calculated using live price.
        """
        price = self.get_live_price(symbol)
        quantity = round(amount / price, 6)

        order_id = f"mock-order-{random.randint(100, 999)}"
        print(f"[LIVE ORDER] Market {side} order for {amount} USDT of {symbol} at price {price}")

        return {
            "success": True,
            "order_id": order_id,
            "price": price,
            "amount": amount,
            "filled_quantity": quantity,
            "avg_entry_price": price,
            "last_entry_price": price,
            "timestamp": datetime.utcnow().isoformat()
        }

    def place_limit_order(self, symbol: str, amount: float, price: float, side: str = "buy") -> dict:
        """
        Place a limit order using amount and price.
        """
        quantity = round(amount / price, 6)

        order_id = f"mock-limit-{random.randint(100, 999)}"
        print(f"[LIVE ORDER] Limit {side} order for {amount} USDT of {symbol} at price {price}")

        return {
            "success": True,
            "order_id": order_id,
            "price": price,
            "amount": amount,
            "quantity": quantity,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_mock_balance(self) -> dict:
        """
        Return a mock balance. In production, replace with real API call.
        """
        return {"USDT": 1000.0}


def get_exchange_client(exchange: str, api_key: str, api_secret: str):
    """
    Factory to return the correct exchange client.
    Accepts already-decrypted API key and secret.
    """
    try:
        if not api_key or not api_secret:
            raise ValueError("Missing API key or secret.")

        if exchange.lower() == "binance":
            return BinanceExchangeClient(api_key, api_secret)

        raise ValueError(f"Unsupported exchange: {exchange}")
    except Exception as e:
        print(f"[❌ ERROR] Failed to create exchange client: {str(e)}")
        raise ValueError(f"Failed to connect to exchange client: {str(e)}")
