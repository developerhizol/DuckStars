# keyboards/profile.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Пользовательское соглашение",
            url="https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19",
            icon_custom_emoji_id="5766994197705921104"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Политика конфиденциальности",
            url="https://telegra.ph/Politika-konfidencialnosti-04-01-26",
            icon_custom_emoji_id="6037249452824072506"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="back_to_main",
            icon_custom_emoji_id="5258236805890710909"
        ),
        width=1
    )
    
    return builder.as_markup()