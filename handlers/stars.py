# handlers/stars.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp

from keyboards.stars import (
    get_stars_recipient_keyboard,
    get_stars_quantity_keyboard,
    get_stars_friend_keyboard,
    get_stars_payment_keyboard
)
from utils.states import StarsStates
from utils.database import add_purchase

router = Router()

STARS_IMAGE_URL = "https://keephere.ru/get/BNSVYRIcDNp/o/photo.jpg"
PAYMENT_IMAGE_URL = "https://keephere.ru/get/DNSVc06HK7h/o/photo.jpg"
HEART_EFFECT_ID = "5159385139981059251"

@router.callback_query(F.data == "buy_stars")
async def buy_stars(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_recipient)
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<i>Выберите получателя звёзд:</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(STARS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="stars.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_stars_recipient_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stars_self")
async def stars_self(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_quantity)
    await state.update_data(recipient=f"@{callback.from_user.username or callback.from_user.id}")
    await state.update_data(is_friend=False)
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>@{callback.from_user.username or callback.from_user.id}</b>\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"<i>Выберите необходимый пакет или введите числом от 50 до 10.000</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(STARS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="stars.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_stars_quantity_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()

@router.callback_query(F.data == "stars_friend")
async def stars_friend(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_quantity)
    await state.update_data(is_friend=True)
    
    text = (
        f"<b>Введите имя пользователя человека, которому хотите подарить звезды</b>"
    )
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML"
    )
    await callback.message.edit_reply_markup(
        reply_markup=get_stars_friend_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()

@router.message(StarsStates.choose_quantity)
async def stars_quantity_input(message: Message, state: FSMContext):
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
                f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
                f"<b>Покупка звёзд</b>\n"
                f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
                f"<b>Получатель:</b> <b>{username}</b>\n\n"
                f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
                f"<i>Выберите необходимый пакет или введите числом от 50 до 10.000</i>"
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.get(STARS_IMAGE_URL) as response:
                    image_data = await response.read()
            
            try:
                await message.bot.edit_message_media(
                    media=InputMediaPhoto(
                        media=BufferedInputFile(image_data, filename="stars.jpg"),
                        caption=text,
                        parse_mode="HTML"
                    ),
                    chat_id=message.chat.id,
                    message_id=bot_message_id,
                    reply_markup=get_stars_quantity_keyboard()
                )
                await state.update_data(bot_message_id=bot_message_id)
            except Exception as e:
                await message.answer("Произошла ошибка, попробуйте снова", message_effect_id=HEART_EFFECT_ID)
        else:
            await message.delete()
            await message.answer("<b>Пожалуйста, введите корректный @username</b>", parse_mode="HTML")
    else:
        try:
            stars = int(message.text)
            if 50 <= stars <= 10000:
                price = stars * 1.45
                await state.update_data(stars=stars, price=price)
                await state.set_state(StarsStates.choose_payment)
                
                data = await state.get_data()
                purchase_id = add_purchase(
                    user_id=message.from_user.id,
                    type="stars",
                    item=f"{stars} звёзд",
                    amount=price,
                    stars=stars,
                    recipient=data.get('recipient')
                )
                await state.update_data(purchase_id=purchase_id)
                
                await message.delete()
                
                text = (
                    f"<blockquote><tg-emoji emoji-id='5312361253610475399'>🛒</tg-emoji> <b>Ваш товар:</b> {stars} звёзд\n"
                    f"<tg-emoji emoji-id='5197434882321567830'>💵</tg-emoji> <b>Стоимость покупки:</b> {price:.2f}₽</blockquote>\n\n"
                    f"<tg-emoji emoji-id='5470177992950946662'>👇</tg-emoji> <i>Выберите способ оплаты</i>"
                )
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(PAYMENT_IMAGE_URL) as response:
                        image_data = await response.read()
                
                try:
                    await message.bot.edit_message_media(
                        media=InputMediaPhoto(
                            media=BufferedInputFile(image_data, filename="payment.jpg"),
                            caption=text,
                            parse_mode="HTML"
                        ),
                        chat_id=message.chat.id,
                        message_id=bot_message_id,
                        reply_markup=get_stars_payment_keyboard()
                    )
                except Exception as e:
                    await message.answer("Произошла ошибка, попробуйте снова", message_effect_id=HEART_EFFECT_ID)
            else:
                await message.delete()
                await message.answer("<b>Пожалуйста, введите число от 50 до 10.000</b>", parse_mode="HTML")
        except ValueError:
            await message.delete()

@router.callback_query(F.data.startswith("stars_qty_"))
async def stars_quantity_select(callback: CallbackQuery, state: FSMContext):
    stars = int(callback.data.split("_")[2])
    price = stars * 1.45
    
    await state.update_data(stars=stars, price=price)
    await state.set_state(StarsStates.choose_payment)
    
    data = await state.get_data()
    purchase_id = add_purchase(
        user_id=callback.from_user.id,
        type="stars",
        item=f"{stars} звёзд",
        amount=price,
        stars=stars,
        recipient=data.get('recipient')
    )
    await state.update_data(purchase_id=purchase_id)
    
    text = (
        f"<blockquote><tg-emoji emoji-id='5312361253610475399'>🛒</tg-emoji> <b>Ваш товар:</b> {stars} звёзд\n"
        f"<tg-emoji emoji-id='5197434882321567830'>💵</tg-emoji> <b>Стоимость покупки:</b> {price:.2f}₽</blockquote>\n\n"
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
        reply_markup=get_stars_payment_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stars_back")
async def stars_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_recipient)
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<i>Выберите получателя звёзд:</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(STARS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="stars.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_stars_recipient_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stars_back_to_qty")
async def stars_back_to_qty(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_quantity)
    await state.update_data(is_friend=False)
    
    data = await state.get_data()
    recipient = data.get('recipient', f"@{callback.from_user.username or callback.from_user.id}")
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>{recipient}</b>\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"<i>Выберите необходимый пакет или введите числом от 50 до 10.000</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(STARS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="stars.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_stars_quantity_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()