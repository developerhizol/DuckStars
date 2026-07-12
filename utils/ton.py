# utils/ton.py
import aiohttp
import logging
import base64
import time
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class TonAPI:
    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address
        self.base_url = "https://toncenter.com/api/v2"
    
    async def get_transactions(self, limit: int = 30) -> Optional[List[Dict]]:
        """Получение последних транзакций кошелька"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/getTransactions"
            params = {
                "address": self.wallet_address,
                "limit": limit,
                "archival": "true"
            }
            try:
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    if data.get("ok"):
                        return data.get("result", [])
                    else:
                        logger.error(f"TON API error: {data}")
                        return None
            except Exception as e:
                logger.error(f"Error getting TON transactions: {e}")
                return None
    
    async def check_payment_by_comment(self, user_id: int, min_amount: float = 0.1, max_age_seconds: int = 180) -> Optional[Dict]:
        """
        Проверяет транзакцию по комментарию (ID пользователя)
        max_age_seconds - максимальный возраст транзакции в секундах (по умолчанию 3 минуты)
        """
        transactions = await self.get_transactions(30)
        if not transactions:
            logger.info("No transactions found")
            return None
        
        comment = str(user_id)
        current_time = int(time.time())
        logger.info(f"Looking for comment: {comment}, current_time: {current_time}")
        
        for tx in transactions:
            in_msg = tx.get("in_msg", {})
            
            tx_comment = in_msg.get("message", "")
            
            if not tx_comment:
                msg_data = in_msg.get("msg_data", {})
                if msg_data.get("@type") == "msg.dataText":
                    try:
                        decoded = base64.b64decode(msg_data.get("text", "")).decode('utf-8')
                        tx_comment = decoded
                    except:
                        pass
            
            amount_nano = int(in_msg.get("value", 0))
            amount = amount_nano / 1e9
            
            tx_time = tx.get("utime", 0)
            age = current_time - tx_time
            
            tx_hash = tx.get("transaction_id", {}).get("hash", "")
            
            logger.info(f"Comment: '{tx_comment}', Amount: {amount} TON, Age: {age} seconds, Hash: {tx_hash}")
            
            if tx_comment == comment and amount >= min_amount and age <= max_age_seconds:
                return {
                    "hash": tx_hash,
                    "amount": amount,
                    "timestamp": tx_time,
                    "from": in_msg.get("source"),
                    "to": tx.get("address", {}).get("account_address"),
                    "comment": tx_comment,
                    "age": age
                }
        
        logger.info(f"No fresh transaction with comment '{comment}' found")
        return None