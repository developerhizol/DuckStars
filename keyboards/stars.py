from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_stars_recipient_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Купить себе",
            callback_data="stars_self",
            icon_custom_emoji_id="5357423427709838027"
        ),
        InlineKeyboardButton(
            text="Купить другу",
            callback_data="stars_friend",
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

def get_stars_quantity_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    packages = [
        ("50", "72.5"),
        ("100", "145"),
        ("250", "362.5"),
        ("500", "725"),
        ("1000", "1450"),
        ("2500", "3625")
    ]
    
    for stars, price in packages:
        builder.row(
            InlineKeyboardButton(
                text=f"⭐ {stars} звёзд - {price} ₽",
                callback_data=f"stars_qty_{stars}"
            ),
            width=1
        )
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="stars_back",
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

def get_stars_friend_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="stars_back",
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

def get_stars_payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="СБП (8%)",
            callback_data="payment_sbp",
            icon_custom_emoji_id="5386752951920393980"
        ),
        InlineKeyboardButton(
            text="Карта (8%)",
            callback_data="payment_card",
            icon_custom_emoji_id="5445353829304387411"
        ),
        width=2
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Ton (0%)",
            callback_data="payment_ton",
            icon_custom_emoji_id="5323477509440840402"
        ),
        InlineKeyboardButton(
            text="CryptoBot (3%)",
            callback_data="payment_crypto",
            icon_custom_emoji_id="5361914370068613491"
        ),
        width=2
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="stars_back_to_qty",
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