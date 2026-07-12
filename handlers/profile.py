# handlers/profile.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import os

from keyboards.profile import get_profile_keyboard
from utils.database import get_user_stats

router = Router()

def get_image(filename: str) -> BufferedInputFile:
    path = os.path.join("imgs", filename)
    with open(path, "rb") as f:
        return BufferedInputFile(f.read(), filename=filename)

@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    stats = get_user_stats(user_id)
    
    text = (
        f"<tg-emoji emoji-id='5884366771913233289'>🆔</tg-emoji> "
        f"<b>ID:</b> <code>{user_id}</code>\n"
        f"<tg-emoji emoji-id='5348392971207194994'>💰</tg-emoji> "
        f"<b>Сумма покупок:</b> <code>{stats['total_spent']:.2f} ₽</code>\n"
        f"<tg-emoji emoji-id='6026271988861902412'>🔢</tg-emoji> "
        f"<b>Количество покупок:</b> <code>{stats['total_purchases']}</code>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("profile.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_profile_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "reviews")
async def reviews(callback: CallbackQuery):
    await callback.answer("✍️ Отзывы о нас в разработке", show_alert=True)