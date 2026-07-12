from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import os
import random
import asyncio
import logging

from keyboards.stars import (
    get_stars_recipient_keyboard,
    get_stars_quantity_keyboard,
    get_stars_friend_keyboard,
    get_stars_payment_keyboard
)
from utils.states import StarsStates
from utils.database import add_purchase, get_purchase_by_id, mark_purchase_completed_with_data
from utils.fragapi import FragAPI
from dotenv import load_dotenv

load_dotenv()

router = Router()
logger = logging.getLogger(__name__)

HEART_EFFECT_ID = "5159385139981059251"
ERROR_EMOJI_ID = "5258318620722733379"

FRAGAPI_TOKEN = os.getenv("FRAGAPI_TOKEN")
frag_api = FragAPI(FRAGAPI_TOKEN)

def get_image(filename: str) -> BufferedInputFile:
    path = os.path.join("imgs", filename)
    with open(path, "rb") as f:
        return BufferedInputFile(f.read(), filename=filename)

@router.callback_query(F.data == "buy_stars")
async def buy_stars(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_recipient)
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<i>Выберите получателя звёзд:</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("stars.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_stars_recipient_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stars_self")
async def stars_self(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_quantity)
    await state.update_data(recipient=callback.from_user.username or str(callback.from_user.id))
    await state.update_data(is_friend=False)
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>@{callback.from_user.username or callback.from_user.id}</b>\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"<i>Выберите необходимый пакет или введите числом от 50 до 10.000</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("stars.jpg"),
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
        f"<b>Введите имя пользователя человека, которому хотите подарить звезды</b>\n\n"
        f"<i>Например: @username</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("stars.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
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
            username = message.text[1:]
            await message.delete()
            
            recipient_info = await frag_api.check_stars_recipient(username)
            
            if not recipient_info:
                await message.answer(
                    f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                    f"<b>Пользователь {message.text} не найден</b>",
                    parse_mode="HTML"
                )
                return
            
            await state.update_data(recipient=username)
            await state.update_data(is_friend=False)
            
            text = (
                f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
                f"<b>Покупка звёзд</b>\n"
                f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
                f"<b>Получатель:</b> <b>@{username}</b>\n\n"
                f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
                f"<i>Выберите необходимый пакет или введите числом от 50 до 10.000</i>"
            )
            
            try:
                await message.bot.edit_message_media(
                    media=InputMediaPhoto(
                        media=get_image("stars.jpg"),
                        caption=text,
                        parse_mode="HTML"
                    ),
                    chat_id=message.chat.id,
                    message_id=bot_message_id,
                    reply_markup=get_stars_quantity_keyboard()
                )
                await state.update_data(bot_message_id=bot_message_id)
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                await message.answer("Произошла ошибка, попробуйте снова", message_effect_id=HEART_EFFECT_ID)
        else:
            await message.delete()
            await message.answer(
                "<b>Пожалуйста, введите корректный @username</b>",
                parse_mode="HTML"
            )
    else:
        try:
            stars = int(message.text)
            if 50 <= stars <= 10000:
                await message.delete()
                
                await state.update_data(stars=stars)
                await state.set_state(StarsStates.choose_payment)
                
                data = await state.get_data()
                purchase_id = add_purchase(
                    user_id=message.from_user.id,
                    type="stars",
                    item=f"{stars} звёзд",
                    amount=0,
                    stars=stars,
                    recipient=data.get('recipient')
                )
                await state.update_data(purchase_id=purchase_id)
                
                purchase = get_purchase_by_id(purchase_id)
                order_number = purchase['order_number'] if purchase else str(random.randint(10000, 99999))
                await state.update_data(order_number=order_number)
                
                asyncio.create_task(check_balance_and_update_stars(message, bot_message_id, state, stars, purchase_id))
                
            else:
                await message.delete()
                await message.answer(
                    "<b>Пожалуйста, введите число от 50 до 10.000</b>",
                    parse_mode="HTML"
                )
        except ValueError:
            await message.delete()
            await message.answer(
                "<b>Пожалуйста, введите число</b>",
                parse_mode="HTML"
            )

@router.callback_query(F.data.startswith("stars_qty_"))
async def stars_quantity_select(callback: CallbackQuery, state: FSMContext):
    stars = int(callback.data.split("_")[2])
    
    await state.update_data(stars=stars)
    await state.set_state(StarsStates.choose_payment)
    
    data = await state.get_data()
    purchase_id = add_purchase(
        user_id=callback.from_user.id,
        type="stars",
        item=f"{stars} звёзд",
        amount=0,
        stars=stars,
        recipient=data.get('recipient')
    )
    await state.update_data(purchase_id=purchase_id)
    
    purchase = get_purchase_by_id(purchase_id)
    order_number = purchase['order_number'] if purchase else str(random.randint(10000, 99999))
    await state.update_data(order_number=order_number)
    
    await callback.answer()
    
    asyncio.create_task(check_balance_and_update(callback, state, stars, purchase_id))

@router.callback_query(F.data == "stars_back")
async def stars_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StarsStates.choose_recipient)
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<i>Выберите получателя звёзд:</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("stars.jpg"),
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
    recipient = data.get('recipient', callback.from_user.username or str(callback.from_user.id))
    
    text = (
        f"<tg-emoji emoji-id='5967512159033234930'>⭐️</tg-emoji> "
        f"<b>Покупка звёзд</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>@{recipient}</b>\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"<i>Выберите необходимый пакет или введите числом от 50 до 10.000</i>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("stars.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_stars_quantity_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()

async def check_balance_and_update(callback: CallbackQuery, state: FSMContext, stars: int, purchase_id: int):
    try:
        me = await frag_api.get_me()
        logger.info(f"FragAPI balance response: {me}")
        
        if me:
            balance = me.get('balance', 0)
            
            price_ton = stars * 0.001
            price_rub = price_ton * 90
            
            logger.info(f"Balance: {balance} TON, Required: {price_ton} TON")
            
            if balance < price_ton:
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=get_image("stars.jpg"),
                        caption=(
                            f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                            f"<b>У нас нет такого количества звёзд. Укажите меньшее количество или попробуйте позже...</b>"
                        ),
                        parse_mode="HTML"
                    ),
                    reply_markup=get_stars_quantity_keyboard()
                )
                await state.update_data(bot_message_id=callback.message.message_id)
                return
            
            await state.update_data(price=price_rub)
            
            text = (
                f"<blockquote><tg-emoji emoji-id='5312361253610475399'>🛒</tg-emoji> <b>Ваш товар:</b> {stars} звёзд\n"
                f"<tg-emoji emoji-id='5197434882321567830'>💵</tg-emoji> <b>Стоимость покупки:</b> {price_rub:.2f}₽</blockquote>\n\n"
                f"<tg-emoji emoji-id='5470177992950946662'>👇</tg-emoji> <i>Выберите способ оплаты</i>"
            )
            
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=get_image("choose_payment.jpg"),
                    caption=text,
                    parse_mode="HTML"
                ),
                reply_markup=get_stars_payment_keyboard()
            )
        else:
            logger.error("Failed to get FragAPI balance")
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=get_image("stars.jpg"),
                    caption=(
                        f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                        f"<b>Ошибка проверки баланса. Попробуйте позже.</b>"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=get_stars_quantity_keyboard()
            )
            await state.update_data(bot_message_id=callback.message.message_id)
    except Exception as e:
        logger.error(f"Error in check_balance_and_update: {e}")
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=get_image("stars.jpg"),
                caption=(
                    f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                    f"<b>Ошибка проверки баланса. Попробуйте позже.</b>"
                ),
                parse_mode="HTML"
            ),
            reply_markup=get_stars_quantity_keyboard()
        )
        await state.update_data(bot_message_id=callback.message.message_id)

async def check_balance_and_update_stars(message: Message, bot_message_id: int, state: FSMContext, stars: int, purchase_id: int):
    try:
        me = await frag_api.get_me()
        logger.info(f"FragAPI balance response: {me}")
        
        if me:
            balance = me.get('balance', 0)
            
            price_ton = stars * 0.001
            price_rub = price_ton * 90
            
            logger.info(f"Balance: {balance} TON, Required: {price_ton} TON")
            
            if balance < price_ton:
                try:
                    await message.bot.edit_message_media(
                        media=InputMediaPhoto(
                            media=get_image("stars.jpg"),
                            caption=(
                                f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                                f"<b>У нас нет такого количества звёзд. Укажите меньшее количество или попробуйте позже...</b>"
                            ),
                            parse_mode="HTML"
                        ),
                        chat_id=message.chat.id,
                        message_id=bot_message_id,
                        reply_markup=get_stars_quantity_keyboard()
                    )
                except:
                    pass
                return
            
            await state.update_data(price=price_rub)
            
            text = (
                f"<blockquote><tg-emoji emoji-id='5312361253610475399'>🛒</tg-emoji> <b>Ваш товар:</b> {stars} звёзд\n"
                f"<tg-emoji emoji-id='5197434882321567830'>💵</tg-emoji> <b>Стоимость покупки:</b> {price_rub:.2f}₽</blockquote>\n\n"
                f"<tg-emoji emoji-id='5470177992950946662'>👇</tg-emoji> <i>Выберите способ оплаты</i>"
            )
            
            try:
                await message.bot.edit_message_media(
                    media=InputMediaPhoto(
                        media=get_image("choose_payment.jpg"),
                        caption=text,
                        parse_mode="HTML"
                    ),
                    chat_id=message.chat.id,
                    message_id=bot_message_id,
                    reply_markup=get_stars_payment_keyboard()
                )
            except:
                pass
        else:
            try:
                await message.bot.edit_message_media(
                    media=InputMediaPhoto(
                        media=get_image("stars.jpg"),
                        caption=(
                            f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                            f"<b>Ошибка проверки баланса. Попробуйте позже.</b>"
                        ),
                        parse_mode="HTML"
                    ),
                    chat_id=message.chat.id,
                    message_id=bot_message_id,
                    reply_markup=get_stars_quantity_keyboard()
                )
            except:
                pass
    except Exception as e:
        logger.error(f"Error in check_balance_and_update_stars: {e}")
        try:
            await message.bot.edit_message_media(
                media=InputMediaPhoto(
                    media=get_image("stars.jpg"),
                    caption=(
                        f"<tg-emoji emoji-id='{ERROR_EMOJI_ID}'>🚫</tg-emoji> "
                        f"<b>Ошибка проверки баланса. Попробуйте позже.</b>"
                    ),
                    parse_mode="HTML"
                ),
                chat_id=message.chat.id,
                message_id=bot_message_id,
                reply_markup=get_stars_quantity_keyboard()
            )
        except:
            pass

async def execute_stars_purchase(purchase_id: int):
    purchase = get_purchase_by_id(purchase_id)
    if not purchase or purchase['status'] == 'completed':
        return
    
    recipient = purchase.get('recipient')
    stars = purchase.get('stars', 0)
    
    if not recipient or stars <= 0:
        return
    
    result = await frag_api.buy_stars(recipient, stars)
    
    if result and 'error' not in result:
        transaction_id = result.get('transactionId', '')
        message_hash = result.get('messageHash', '')
        mark_purchase_completed_with_data(purchase_id, transaction_id, message_hash)
        return True, result
    else:
        return False, result