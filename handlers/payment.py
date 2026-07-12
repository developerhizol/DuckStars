# handlers/payment.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext

from utils.database import complete_purchase, get_purchase_by_id

router = Router()
REVIEWS_WEBAPP_URL = "https://duckstars.bothost.tech/"

@router.callback_query(F.data.startswith("payment_"))
async def payment_methods(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    methods = {
        "sbp": "СБП",
        "card": "банковская карта",
        "ton": "Ton",
        "crypto": "CryptoBot"
    }
    
    data = await state.get_data()
    purchase_id = data.get('purchase_id')
    
    if purchase_id:
        complete_purchase(purchase_id)
        await state.clear()
        await callback.answer(f"✅ Оплата через {methods.get(method, 'выбранный способ')} успешно завершена!", show_alert=True)
        
        # Получаем данные покупки
        purchase = get_purchase_by_id(purchase_id)
        review_url = f"{REVIEWS_WEBAPP_URL}?action=write&user_id={callback.from_user.id}&purchase_id={purchase_id}"
        
        # Отправляем просьбу об отзыве сразу после покупки
        await callback.message.answer(
            f"<tg-emoji emoji-id='5444887644964159628'>💗</tg-emoji> <b>Благодарим вас за покупку :)</b>\n\n"
            f"<b>Мы искренне надеемся, что вам понравился наш сервис и вы остались довольны полученной услугой.</b>\n\n"
            f"<tg-emoji emoji-id='5447510826304959724'>💬</tg-emoji> <b>Пожалуйста, оставьте отзыв о нашей работе. Это будет полезно для будущих клиентов, которые ищут информацию о нас.</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Оставить отзыв",
                        web_app=WebAppInfo(url=review_url),
                        icon_custom_emoji_id="5470060791883374114"
                    )],
                    [InlineKeyboardButton(
                        text="Главное меню",
                        callback_data="back_to_main",
                        icon_custom_emoji_id="5257963315258204021"
                    )]
                ]
            )
        )
    else:
        await callback.answer(f"⏳ Оплата через {methods.get(method, 'выбранный способ')} в разработке...", show_alert=True)