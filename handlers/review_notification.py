# handlers/review_notification.py
from aiogram import Router, Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import asyncio
import logging

from utils.database import get_purchases_for_review_notification, mark_review_notification_sent, get_purchase_by_id

router = Router()
logger = logging.getLogger(__name__)

REVIEWS_WEBAPP_URL = "https://duckstars.bothost.tech/"

async def check_and_send_review_notifications(bot: Bot):
    while True:
        try:
            purchases = get_purchases_for_review_notification()
            
            for purchase in purchases:
                try:
                    review_url = f"{REVIEWS_WEBAPP_URL}?action=write&user_id={purchase['user_id']}&purchase_id={purchase['id']}"
                    
                    await bot.send_message(
                        chat_id=purchase['user_id'],
                        text=(
                            f"<tg-emoji emoji-id='5444887644964159628'>💗</tg-emoji> <b>Благодарим вас за покупку :)</b>\n\n"
                            f"<b>Мы искренне надеемся, что вам понравился наш сервис и вы остались довольны полученной услугой.</b>\n\n"
                            f"<tg-emoji emoji-id='5447510826304959724'>💬</tg-emoji> <b>Пожалуйста, оставьте отзыв о нашей работе. Это будет полезно для будущих клиентов, которые ищут информацию о нас.</b>"
                        ),
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=[
                                [InlineKeyboardButton(
                                    text="Оставить отзыв",
                                    web_app=WebAppInfo(url=review_url),
                                    icon_custom_emoji_id="5470060791883374114"
                                )],
                                [InlineKeyboardButton(
                                    text="Главное меню",
                                    callback_data="back_to_main",
                                    icon_custom_emoji_id="5257963315258204021"
                                )]
                            ]
                        )
                    )
                    
                    mark_review_notification_sent(purchase['id'])
                    logger.info(f"Отправлено уведомление об отзыве для покупки #{purchase['id']}")
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления для покупки #{purchase['id']}: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче уведомлений: {e}")
        
        await asyncio.sleep(60)