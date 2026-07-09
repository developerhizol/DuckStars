# keyboards/premium.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_premium_recipient_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Купить себе",
            callback_data="premium_self",
            icon_custom_emoji_id="5357423427709838027"
        ),
        InlineKeyboardButton(
            text="Купить другу",
            callback_data="premium_friend",
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

def get_premium_friend_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="premium_back",
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

def get_premium_duration_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="3 месяца - 1099₽",
            callback_data="premium_3",
            icon_custom_emoji_id="5319069159303194146"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="6 месяцев - 1449₽",
            callback_data="premium_6",
            icon_custom_emoji_id="5319069159303194146"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="12 месяцев - 2499₽",
            callback_data="premium_12",
            icon_custom_emoji_id="5319069159303194146"
        ),
        width=1
    )
    
    builder.row(
        InlineKeyboardButton(
            text="Назад",
            callback_data="premium_back",
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

def get_premium_payment_keyboard() -> InlineKeyboardMarkup:
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
            callback_data="premium_back_to_duration",
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