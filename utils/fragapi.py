import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class FragAPI:
    BASE_URL = "https://api.fragapi.com/v1"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        logger.info(f"FragAPI initialized with token: {token[:10]}...")
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        logger.info("Getting FragAPI balance...")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.BASE_URL}/users/me",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    logger.info(f"FragAPI response status: {response.status}")
                    data = await response.json()
                    logger.info(f"FragAPI response: {data}")
                    if response.status == 200:
                        logger.info(f"FragAPI balance: {data.get('balance', 0)}")
                        return data
                    else:
                        logger.error(f"FragAPI get_me error: {data}")
                        return None
            except asyncio.TimeoutError:
                logger.error("FragAPI timeout")
                return None
            except Exception as e:
                logger.error(f"FragAPI get_me exception: {e}")
                return None
    
    async def check_stars_recipient(self, username: str, quantity: int = None) -> Optional[Dict[str, Any]]:
        logger.info(f"Checking stars recipient: {username}, quantity: {quantity}")
        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE_URL}/stars/recipient/{username}"
            if quantity:
                url += f"?quantity={quantity}"
            try:
                async with session.get(url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    data = await response.json()
                    if response.status == 200:
                        logger.info(f"Stars recipient found: {data}")
                        return data
                    else:
                        logger.error(f"FragAPI check_stars_recipient error: {data}")
                        return None
            except Exception as e:
                logger.error(f"FragAPI check_stars_recipient exception: {e}")
                return None
    
    async def check_premium_recipient(self, username: str) -> Optional[Dict[str, Any]]:
        logger.info(f"Checking premium recipient: {username}")
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.BASE_URL}/premium/recipient/{username}",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    data = await response.json()
                    if response.status == 200:
                        logger.info(f"Premium recipient found: {data}")
                        return data
                    else:
                        logger.error(f"FragAPI check_premium_recipient error: {data}")
                        return None
            except Exception as e:
                logger.error(f"FragAPI check_premium_recipient exception: {e}")
                return None
    
    async def buy_stars(self, username: str, quantity: int) -> Optional[Dict[str, Any]]:
        logger.info(f"Buying {quantity} stars for {username}")
        async with aiohttp.ClientSession() as session:
            payload = {
                "username": username,
                "quantity": quantity
            }
            try:
                async with session.post(
                    f"{self.BASE_URL}/stars/buy",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    data = await response.json()
                    if response.status == 200:
                        logger.info(f"Stars bought: {quantity} for {username}")
                        return data
                    else:
                        logger.error(f"FragAPI buy_stars error: {data}")
                        if response.status == 422:
                            error_msg = data.get('message', '')
                            if 'insufficient' in error_msg.lower() or 'balance' in error_msg.lower():
                                return {"error": "insufficient_balance", "message": error_msg}
                        return None
            except Exception as e:
                logger.error(f"FragAPI buy_stars exception: {e}")
                return None
    
    async def buy_premium(self, username: str, months: int) -> Optional[Dict[str, Any]]:
        logger.info(f"Buying {months} months premium for {username}")
        async with aiohttp.ClientSession() as session:
            payload = {
                "username": username,
                "months": months
            }
            try:
                async with session.post(
                    f"{self.BASE_URL}/premium/buy",
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    data = await response.json()
                    if response.status == 200:
                        logger.info(f"Premium bought: {months} months for {username}")
                        return data
                    else:
                        logger.error(f"FragAPI buy_premium error: {data}")
                        if response.status == 422:
                            error_msg = data.get('message', '')
                            if 'insufficient' in error_msg.lower() or 'balance' in error_msg.lower():
                                return {"error": "insufficient_balance", "message": error_msg}
                        return None
            except Exception as e:
                logger.error(f"FragAPI buy_premium exception: {e}")
                return None