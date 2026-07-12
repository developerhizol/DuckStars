# handlers/start.py
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import os

from keyboards.main_menu import get_main_menu_keyboard
from utils.database import create_user, get_user

router = Router()

HEART_EFFECT_ID = "5159385139981059251"

def get_image(filename: str) -> BufferedInputFile:
    path = os.path.join("imgs", filename)
    with open(path, "rb") as f:
        return BufferedInputFile(f.read(), filename=filename)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    user = get_user(user_id)
    if not user:
        create_user(user_id, username, first_name, last_name)
    
    user_name = first_name or "Гость"
    
    greeting_text = (
        f"<tg-emoji emoji-id='5472427507842032538'>👋</tg-emoji> "
        f"<b>{user_name}, добро пожаловать в DuckStars</b>\n\n"
        f"<tg-emoji emoji-id='5417969813609795944'>⭐️</tg-emoji> "
        f"<b>У нас Вы можете приобрести Telegram Stars и Telegram Premium на свой аккаунт за рубли</b>\n\n"
        f"<tg-emoji emoji-id='5472299818464321370'>🛍️</tg-emoji> "
        f"<b>Хороших покупок!</b>"
    )
    
    await message.answer_photo(
        photo=get_image("welcome.jpg"),
        caption=greeting_text,
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML",
        message_effect_id=HEART_EFFECT_ID
    )