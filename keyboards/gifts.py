# keyboards/gifts.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_gifts_recipient_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Купить себе",
            callback_data="gifts_self",
            icon_custom_emoji_id="5357423427709838027"
        ),
        InlineKeyboardButton(
            text="Купить другу",
            callback_data="gifts_friend",
            icon_custom_emoji_id="5357080225463149588"
        ),
        width=2
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

def get_gifts_friend_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="gifts_back",
            icon_custom_emoji_id="5258236805890710909"
        ),
        InlineKeyboardButton(
            text="Меню",
            callback_data="back_to_main",
            icon_custom_emoji_id="5257963315258204021"
        ),
        width=2
    )
    
    return builder.as_markup()

def get_gifts_anonymity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Да",
            callback_data="gifts_anon_yes"
        ),
        InlineKeyboardButton(
            text="Нет",
            callback_data="gifts_anon_no"
        ),
        width=2
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="gifts_back",
            icon_custom_emoji_id="5258236805890710909"
        ),
        InlineKeyboardButton(
            text="Меню",
            callback_data="back_to_main",
            icon_custom_emoji_id="5257963315258204021"
        ),
        width=2
    )
    
    return builder.as_markup()

def get_gifts_list_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Первый ряд: 🎄 и 🎅
    builder.row(
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_tree",
            icon_custom_emoji_id="5345935030143196497"
        ),
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_santa",
            icon_custom_emoji_id="5289761157173775507"
        ),
        width=2
    )
    
    # Второй ряд: 🐒 и 👻
    builder.row(
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_monkey",
            icon_custom_emoji_id="5379850840691476775"
        ),
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_ghost",
            icon_custom_emoji_id="5393309541620291208"
        ),
        width=2
    )
    
    # Третий ряд: 💝 и 🐻‍❄️
    builder.row(
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_heart",
            icon_custom_emoji_id="5224628072619216265"
        ),
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_bear",
            icon_custom_emoji_id="5359736160224586485"
        ),
        width=2
    )
    
    # Четвёртый ряд: 🪅 и 😻
    builder.row(
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_pinata",
            icon_custom_emoji_id="5226661632259691727"
        ),
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_cat",
            icon_custom_emoji_id="5317000922096769303"
        ),
        width=2
    )
    
    # Пятый ряд: 👷‍♂️ (по центру)
    builder.row(
        InlineKeyboardButton(
            text="- 85⭐",
            callback_data="gift_worker",
            icon_custom_emoji_id="5447213743417105726"
        ),
        width=1
    )
    
    # Шестой ряд: Назад и Домой
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="gifts_back_to_anon",
            icon_custom_emoji_id="5258236805890710909"
        ),
        InlineKeyboardButton(
            text="Домой",
            callback_data="back_to_main",
            icon_custom_emoji_id="5257963315258204021"
        ),
        width=2
    )
    
    return builder.as_markup()

def get_gifts_comment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="gifts_back_to_list",
            icon_custom_emoji_id="5258236805890710909"
        ),
        InlineKeyboardButton(
            text="Меню",
            callback_data="back_to_main",
            icon_custom_emoji_id="5257963315258204021"
        ),
        width=2
    )
    
    return builder.as_markup()

def get_gifts_payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Оплатить (телеграм звездами)",
            callback_data="gifts_pay_stars"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="gifts_back_to_comment",
            icon_custom_emoji_id="5258236805890710909"
        ),
        InlineKeyboardButton(
            text="Меню",
            callback_data="back_to_main",
            icon_custom_emoji_id="5257963315258204021"
        ),
        width=2
    )
    
    return builder.as_markup()