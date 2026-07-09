# keyboards/main_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

REVIEWS_WEBAPP_URL = "https://duckstars.bothost.tech/"

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Купить Stars",
            callback_data="buy_stars",
            icon_custom_emoji_id="5967512159033234930"
        ),
        InlineKeyboardButton(
            text="Купить Premium",
            callback_data="buy_premium",
            icon_custom_emoji_id="5929020872579879365"
        ),
        width=2
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Купить удалённые подарки",
            callback_data="buy_gifts",
            icon_custom_emoji_id="5970074171449808121"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Поддержка",
            url="https://t.me/my_support_account",
            icon_custom_emoji_id="5859232223865081255"
        ),
        InlineKeyboardButton(
            text="Профиль",
            callback_data="profile",
            icon_custom_emoji_id="5454280317533691861"
        ),
        width=2
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Отзывы о нас",
            web_app=WebAppInfo(url=REVIEWS_WEBAPP_URL),
            icon_custom_emoji_id="5470060791883374114"
        ),
        width=1
    )
    
    return builder.as_markup()