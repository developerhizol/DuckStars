from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import os
import random
import asyncio

from keyboards.premium import (
    get_premium_recipient_keyboard,
    get_premium_duration_keyboard,
    get_premium_payment_keyboard,
    get_premium_friend_keyboard
)
from utils.states import PremiumStates
from utils.database import add_purchase, get_purchase_by_id, mark_purchase_completed_with_data
from utils.fragapi import FragAPI
from dotenv import load_dotenv

load_dotenv()

router = Router()

HEART_EFFECT_ID = "5159385139981059251"
PREMIUM_EMOJI_ID = "5447381715293074599"
ERROR_EMOJI_ID = "5258318620722733379"

FRAGAPI_TOKEN = os.getenv("FRAGAPI_TOKEN")
frag_api = FragAPI(FRAGAPI_TOKEN)

def get_image(filename: str) -> BufferedInputFile:
    path = os.path.join("imgs", filename)
    with open(path, "rb") as f:
        return BufferedInputFile(f.read(), filename=filename)

@router.callback_query(F.data == "buy_premium")
async def buy_premium(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PremiumStates.choose_recipient)
    
    text = (
        f"<tg-emoji emoji-id='5929020872579879365'>💎</tg-emoji> "
        f"<b>Покупка премиума</b>\n\n"
        f"❗️<b><u>Получить могут только пользователи без активной подписки</u></b>❗️\n\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<i>Выберите получателя премиума:</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("premium.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_premium_recipient_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "premium_self")
async def premium_self(callback: CallbackQuery, state: FSMContext):
    username = callback.from_user.username or str(callback.from_user.id)
    
    recipient_info = await frag_api.check_premium_recipient(username)
    
    if recipient_info:
        await callback.answer(
            "⚠️ У этого аккаунта уже есть telegram premium",
            show_alert=True
        )
        return
    
    await state.set_state(PremiumStates.choose_duration)
    await state.update_data(recipient=username)
    await state.update_data(is_friend=False)
    
    text = (
        f"<tg-emoji emoji-id='5929020872579879365'>👑</tg-emoji> "
        f"<b>Покупка премиум</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>@{username}</b>\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"<i>Выберите необходимый срок:</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("premium.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_premium_duration_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()

@router.callback_query(F.data == "premium_friend")
async def premium_friend(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PremiumStates.choose_duration)
    await state.update_data(is_friend=True)
    
    text = (
        f"<b>Введите имя пользователя человека, которому хотите подарить премиум</b>\n\n"
        f"<i>Например: @username</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("premium.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_premium_friend_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()

@router.message(PremiumStates.choose_duration)
async def premium_username_input(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_message_id = data.get('bot_message_id')
    is_friend = data.get('is_friend', False)
    
    if not bot_message_id:
        await message.delete()
        return
    
    if is_friend:
        if message.text and message.text.startswith('@'):
            username = message.text[1:]
            await message.delete()
            
            recipient_info = await frag_api.check_premium_recipient(username)
            
            if recipient_info:
                await message.answer(
                    f"<tg-emoji emoji-id='{PREMIUM_EMOJI_ID}'>⚠️</tg-emoji> "
                    f"<b>У этого аккаунта уже есть telegram premium</b>",
                    parse_mode="HTML"
                )
                return
            
            await state.update_data(recipient=username)
            await state.update_data(is_friend=False)
            
            text = (
                f"<tg-emoji emoji-id='5929020872579879365'>👑</tg-emoji> "
                f"<b>Покупка премиум</b>\n"
                f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
                f"<b>Получатель:</b> <b>@{username}</b>\n\n"
                f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
                f"<i>Выберите необходимый срок:</i>"
            )
            
            try:
                await message.bot.edit_message_media(
                    media=InputMediaPhoto(
                        media=get_image("premium.jpg"),
                        caption=text,
                        parse_mode="HTML"
                    ),
                    chat_id=message.chat.id,
                    message_id=bot_message_id,
                    reply_markup=get_premium_duration_keyboard()
                )
                await state.update_data(bot_message_id=bot_message_id)
            except Exception as e:
                await message.answer("Произошла ошибка, попробуйте снова", message_effect_id=HEART_EFFECT_ID)
        else:
            await message.delete()
            await message.answer(
                "<b>Пожалуйста, введите корректный @username</b>",
                parse_mode="HTML"
            )
    else:
        await message.delete()

@router.callback_query(F.data.startswith("premium_"))
async def premium_duration_select(callback: CallbackQuery, state: FSMContext):
    if callback.data == "premium_back_to_duration":
        await state.set_state(PremiumStates.choose_duration)
        await state.update_data(is_friend=False)
        
        data = await state.get_data()
        recipient = data.get('recipient', callback.from_user.username or str(callback.from_user.id))
        
        text = (
            f"<tg-emoji emoji-id='5929020872579879365'>👑</tg-emoji> "
            f"<b>Покупка премиум</b>\n"
            f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
            f"<b>Получатель:</b> <b>@{recipient}</b>\n\n"
            f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
            f"<i>Выберите необходимый срок:</i>"
        )
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=get_image("premium.jpg"),
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=get_premium_duration_keyboard()
        )
        await state.update_data(bot_message_id=callback.message.message_id)
        await callback.answer()
        return
    
    if callback.data == "premium_back":
        await state.set_state(PremiumStates.choose_recipient)
        
        text = (
            f"<tg-emoji emoji-id='5929020872579879365'>💎</tg-emoji> "
            f"<b>Покупка премиума</b>\n\n"
            f"❗️<b><u>Получить могут только пользователи без активной подписки</u></b>❗️\n\n"
            f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
            f"<i>Выберите получателя премиума:</i>"
        )
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=get_image("premium.jpg"),
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=get_premium_recipient_keyboard()
        )
        await callback.answer()
        return
    
    months = int(callback.data.split("_")[1])
    prices = {3: 1099, 6: 1449, 12: 2499}
    price = prices.get(months, 1099)
    
    await state.update_data(months=months)
    await state.set_state(PremiumStates.choose_payment)
    
    data = await state.get_data()
    recipient = data.get('recipient', callback.from_user.username or str(callback.from_user.id))
    
    purchase_id = add_purchase(
        user_id=callback.from_user.id,
        type="premium",
        item=f"Premium {months} месяца",
        amount=0,
        recipient=recipient
    )
    await state.update_data(purchase_id=purchase_id)
    
    purchase = get_purchase_by_id(purchase_id)
    order_number = purchase['order_number'] if purchase else str(random.randint(10000, 99999))
    await state.update_data(order_number=order_number)
    
    await callback.answer()
    
    asyncio.create_task(check_balance_and_update_premium(callback, state, months, price, purchase_id))

async def check_balance_and_update_premium(callback: CallbackQuery, state: FSMContext, months: int, price: float, purchase_id: int):
    me = await frag_api.get_me()
    
    if me:
        balance = me.get('balance', 0)
        
        if balance < price:
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=get_image("premium.jpg"),
                    caption=(
                        f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                        f"<b>У нас закончились telegram premium. Выберите меньший срок или попробуйте позже...</b>"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=get_premium_duration_keyboard()
            )
            await state.update_data(bot_message_id=callback.message.message_id)
            return
        
        await state.update_data(price=price)
        
        text = (
            f"<blockquote><tg-emoji emoji-id='5312361253610475399'>🛒</tg-emoji> <b>Ваш товар:</b> Premium {months} месяца\n"
            f"<tg-emoji emoji-id='5197434882321567830'>💵</tg-emoji> <b>Стоимость покупки:</b> {price}₽</blockquote>\n\n"
            f"<tg-emoji emoji-id='5470177992950946662'>👇</tg-emoji> <i>Выберите способ оплаты</i>"
        )
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=get_image("choose_payment.jpg"),
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=get_premium_payment_keyboard()
        )
    else:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=get_image("premium.jpg"),
                caption=(
                    f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                    f"<b>Ошибка проверки баланса. Попробуйте позже.</b>"
                ),
                parse_mode="HTML"
            ),
            reply_markup=get_premium_duration_keyboard()
        )
        await state.update_data(bot_message_id=callback.message.message_id)

async def execute_premium_purchase(purchase_id: int):
    purchase = get_purchase_by_id(purchase_id)
    if not purchase or purchase['status'] == 'completed':
        return
    
    recipient = purchase.get('recipient')
    months = None
    
    item = purchase.get('item', '')
    if '3' in item:
        months = 3
    elif '6' in item:
        months = 6
    elif '12' in item:
        months = 12
    
    if not recipient or not months:
        return
    
    result = await frag_api.buy_premium(recipient, months)
    
    if result and 'error' not in result:
        transaction_id = result.get('transactionId', '')
        message_hash = result.get('messageHash', '')
        mark_purchase_completed_with_data(purchase_id, transaction_id, message_hash)
        return True, result
    else:
        return False, result