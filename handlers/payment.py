# handlers/payment.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from utils.database import complete_purchase

router = Router()

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
        
        await callback.message.answer(
            "🎉 Поздравляем! Вы успешно совершили покупку!\n\n"
            "💬 Через 15 минут мы попросим вас оставить отзыв о нашей работе.",
            reply_markup=None
        )
    else:
        await callback.answer(f"⏳ Оплата через {methods.get(method, 'выбранный способ')} в разработке...", show_alert=True)