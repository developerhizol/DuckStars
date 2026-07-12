# keyboards/main_menu.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

REVIEWS_WEBAPP_URL = "https://duckstars.bothost.tech/"

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Первый ряд: Stars и Premium
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
    
    # Второй ряд: Отзывы о нас (по центру)
    builder.row(
        InlineKeyboardButton(
            text="Отзывы о нас",
            web_app=WebAppInfo(url=REVIEWS_WEBAPP_URL),
            icon_custom_emoji_id="5470060791883374114"
        ),
        width=1
    )
    
    # Третий ряд: Поддержка и Профиль
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
    
    # Четвертый ряд: Наш VPN (по центру)
    builder.row(
        InlineKeyboardButton(
            text="Наш VPN",
            url="https://t.me/streamnetvpnbot",
            icon_custom_emoji_id="5447410659077661506"
        ),
        width=1
    )
    
    return builder.as_markup()