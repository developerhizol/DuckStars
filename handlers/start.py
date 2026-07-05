# handlers/start.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import asyncio

from keyboards.main_menu import get_main_menu_keyboard

router = Router()

WELCOME_STICKER = "CAACAgUAAxkBAAFOS61qSpdR4Hdw4SaSPjkVvfuD05PYfAACXREAAq97UVWRKrlFhzZOKDwE"

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer_sticker(sticker=WELCOME_STICKER)
    await asyncio.sleep(1)
    
    user_name = message.from_user.first_name or "Гость"
    
    greeting_text = (
        f"<tg-emoji emoji-id='5472427507842032538'>👋</tg-emoji> "
        f"<b>{user_name}, добро пожаловать в DuckStars</b>\n\n"
        f"<tg-emoji emoji-id='5417969813609795944'>⭐️</tg-emoji> "
        f"<b>У нас Вы можете приобрести Telegram Stars и Telegram Premium на свой аккаунт за рубли</b>\n\n"
        f"<tg-emoji emoji-id='5472299818464321370'>🛍️</tg-emoji> "
        f"<b>Хороших покупок!</b>"
    )
    
    await message.answer(
        text=greeting_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
