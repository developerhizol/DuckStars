# handlers/premium.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp

from keyboards.premium import (
    get_premium_recipient_keyboard,
    get_premium_duration_keyboard,
    get_premium_payment_keyboard,
    get_premium_friend_keyboard
)
from utils.states import PremiumStates
from utils.database import add_purchase

router = Router()

PREMIUM_IMAGE_URL = "https://keephere.ru/get/hNSVak5QpYi/o/photo.jpg"
PAYMENT_IMAGE_URL = "https://keephere.ru/get/DNSVc06HK7h/o/photo.jpg"
HEART_EFFECT_ID = "5159385139981059251"

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
    
    async with aiohttp.ClientSession() as session:
        async with session.get(PREMIUM_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="premium.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_premium_recipient_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "premium_self")
async def premium_self(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PremiumStates.choose_duration)
    await state.update_data(recipient=f"@{callback.from_user.username or callback.from_user.id}")
    await state.update_data(is_friend=False)
    
    text = (
        f"<tg-emoji emoji-id='5929020872579879365'>👑</tg-emoji> "
        f"<b>Покупка премиум</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>@{callback.from_user.username or callback.from_user.id}</b>\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"<i>Выберите необходимый пакет:</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(PREMIUM_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="premium.jpg"),
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
        f"<b>Введите имя пользователя человека, которому хотите подарить премиум</b>"
    )
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML"
    )
    await callback.message.edit_reply_markup(
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
            username = message.text
            await message.delete()
            
            await state.update_data(recipient=username)
            await state.update_data(is_friend=False)
            
            text = (
                f"<tg-emoji emoji-id='5929020872579879365'>👑</tg-emoji> "
                f"<b>Покупка премиум</b>\n"
                f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
                f"<b>Получатель:</b> <b>{username}</b>\n\n"
                f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
                f"<i>Выберите необходимый пакет:</i>"
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.get(PREMIUM_IMAGE_URL) as response:
                    image_data = await response.read()
            
            try:
                await message.bot.edit_message_media(
                    media=InputMediaPhoto(
                        media=BufferedInputFile(image_data, filename="premium.jpg"),
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
            await message.answer("<b>Пожалуйста, введите корректный @username</b>", parse_mode="HTML")
    else:
        await message.delete()

@router.callback_query(F.data.startswith("premium_"))
async def premium_duration_select(callback: CallbackQuery, state: FSMContext):
    if callback.data == "premium_back_to_duration":
        await state.set_state(PremiumStates.choose_duration)
        await state.update_data(is_friend=False)
        
        data = await state.get_data()
        recipient = data.get('recipient', f"@{callback.from_user.username or callback.from_user.id}")
        
        text = (
            f"<tg-emoji emoji-id='5929020872579879365'>👑</tg-emoji> "
            f"<b>Покупка премиум</b>\n"
            f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
            f"<b>Получатель:</b> <b>{recipient}</b>\n\n"
            f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
            f"<i>Выберите необходимый пакет:</i>"
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.get(PREMIUM_IMAGE_URL) as response:
                image_data = await response.read()
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=BufferedInputFile(image_data, filename="premium.jpg"),
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
        
        async with aiohttp.ClientSession() as session:
            async with session.get(PREMIUM_IMAGE_URL) as response:
                image_data = await response.read()
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=BufferedInputFile(image_data, filename="premium.jpg"),
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=get_premium_recipient_keyboard()
        )
        await callback.answer()
        return
    
    months = callback.data.split("_")[1]
    prices = {"3": 1099, "6": 1449, "12": 2499}
    price = prices[months]
    
    await state.update_data(months=months, price=price)
    await state.set_state(PremiumStates.choose_payment)
    
    data = await state.get_data()
    purchase_id = add_purchase(
        user_id=callback.from_user.id,
        type="premium",
        item=f"Premium {months} месяца",
        amount=price,
        recipient=data.get('recipient')
    )
    await state.update_data(purchase_id=purchase_id)
    
    text = (
        f"<blockquote><tg-emoji emoji-id='5312361253610475399'>🛒</tg-emoji> <b>Ваш товар:</b> Premium {months} месяца\n"
        f"<tg-emoji emoji-id='5197434882321567830'>💵</tg-emoji> <b>Стоимость покупки:</b> {price}₽</blockquote>\n\n"
        f"<tg-emoji emoji-id='5470177992950946662'>👇</tg-emoji> <i>Выберите способ оплаты</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(PAYMENT_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="payment.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_premium_payment_keyboard()
    )
    await callback.answer()