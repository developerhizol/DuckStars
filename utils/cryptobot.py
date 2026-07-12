# utils/cryptobot.py
import aiohttp
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CryptoBotAPI:
    BASE_URL = "https://pay.crypt.bot/api"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Crypto-Pay-API-Token": token,
            "Content-Type": "application/json"
        }
    
    async def create_invoice(
        self,
        amount: float,
        asset: str = "USDT",
        description: str = "Покупка в DuckStars",
        paid_btn_name: str = "callback",
        paid_btn_url: str = None,
        hidden_message: str = None,
        test: bool = True
    ) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            payload = {
                "asset": asset,
                "amount": str(amount),
                "description": description,
                "paid_btn_name": paid_btn_name,
                "paid_btn_url": paid_btn_url or "https://t.me/DucksStarsRobot",
                "test": test
            }
            
            if hidden_message:
                payload["hidden_message"] = hidden_message
            
            async with session.post(
                f"{self.BASE_URL}/createInvoice",
                headers=self.headers,
                json=payload
            ) as response:
                data = await response.json()
                if data.get("ok"):
                    logger.info(f"Invoice created: {data['result']['invoice_id']}")
                    return data["result"]
                else:
                    logger.error(f"Error creating invoice: {data}")
                    return None
    
    async def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            payload = {"invoice_id": invoice_id}
            async with session.post(
                f"{self.BASE_URL}/getInvoices",
                headers=self.headers,
                json=payload
            ) as response:
                data = await response.json()
                if data.get("ok") and data["result"].get("items"):
                    return data["result"]["items"][0]
                return None
    
    async def check_invoice_status(self, invoice_id: int) -> str:
        invoice = await self.get_invoice(invoice_id)
        if invoice:
            return invoice.get("status", "unknown")
        return "not_found"