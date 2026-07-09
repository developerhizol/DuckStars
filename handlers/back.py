# handlers/back.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp

from keyboards.main_menu import get_main_menu_keyboard
from utils.database import delete_temp_purchase

router = Router()
WELCOME_IMAGE_URL = "https://keephere.ru/get/LNSVNaFJxFh/o/photo.jpg"

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    delete_temp_purchase(callback.from_user.id)
    
    user_name = callback.from_user.first_name or "Гость"
    
    greeting_text = (
        f"<tg-emoji emoji-id='5472427507842032538'>👋</tg-emoji> "
        f"<b>{user_name}, добро пожаловать в DuckStars</b>\n\n"
        f"<tg-emoji emoji-id='5417969813609795944'>⭐️</tg-emoji> "
        f"<b>У нас Вы можете приобрести Telegram Stars и Telegram Premium на свой аккаунт за рубли</b>\n\n"
        f"<tg-emoji emoji-id='5472299818464321370'>🛍️</tg-emoji> "
        f"<b>Хороших покупок!</b>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(WELCOME_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="welcome.jpg"),
            caption=greeting_text,
            parse_mode="HTML"
        ),
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()