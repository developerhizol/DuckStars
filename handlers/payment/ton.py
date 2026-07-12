from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp
import uuid
import asyncio
import random
import os
import logging

from utils.database import complete_purchase, get_purchase_by_id, get_user, is_agreement_shown, mark_agreement_shown, update_purchase_invoice
from utils.ton import TonAPI
from handlers.stars import execute_stars_purchase
from handlers.premium import execute_premium_purchase
from dotenv import load_dotenv

load_dotenv()

router = Router()
logger = logging.getLogger(__name__)

TON_WALLET = "UQC1FQ_6meBl0qlVQjFCXEs6mK5EKDduHSE5plyQ314tsSjB"

def get_image(filename: str) -> BufferedInputFile:
    path = os.path.join("imgs", filename)
    with open(path, "rb") as f:
        return BufferedInputFile(f.read(), filename=filename)

EMOJI_IDS = {
    "waiting": "5841359499146825803",
    "processing": "5841243255856960314",
    "done": "5444987348334965906",
    "home": "5257963315258204021"
}

REVIEWS_WEBAPP_URL = "https://duckstars.bothost.tech/"

ton_api = TonAPI(TON_WALLET)

@router.callback_query(F.data == "payment_ton")
async def payment_ton(callback: CallbackQuery, state: FSMContext):
    await process_ton_payment(callback, state)

async def get_ton_price() -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://pay.crypt.bot/api/getExchangeRates",
            headers={"Crypto-Pay-API-Token": os.getenv("CRYPTOBOT_TOKEN")}
        ) as response:
            data = await response.json()
            if data.get("ok"):
                for rate in data.get("result", []):
                    if rate.get("source") == "TON" and rate.get("target") == "RUB":
                        return float(rate.get("rate"))
    return 150.0

async def process_ton_payment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    purchase_id = data.get('purchase_id')
    order_number = data.get('order_number', str(random.randint(10000, 99999)))
    
    if not purchase_id:
        await callback.answer("❌ Ошибка: покупка не найдена", show_alert=True)
        return
    
    purchase = get_purchase_by_id(purchase_id)
    if not purchase:
        await callback.answer("❌ Ошибка: покупка не найдена", show_alert=True)
        return
    
    user = get_user(callback.from_user.id)
    if user:
        username = user.get('username') or callback.from_user.username or str(callback.from_user.id)
    else:
        username = callback.from_user.username or str(callback.from_user.id)
    
    transaction_id = str(uuid.uuid4())
    await state.update_data(transaction_id=transaction_id)
    await state.update_data(payment_method="ton")
    
    loading_text = f"<tg-emoji emoji-id='{EMOJI_IDS['waiting']}'>⏳</tg-emoji> <b>Генерируем счёт для оплаты...</b>"
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("loading.jpg"),
            caption=loading_text,
            parse_mode="HTML"
        ),
        reply_markup=None
    )
    
    rate = await get_ton_price()
    ton_amount = round(purchase['amount'] / rate, 4)
    if ton_amount < 0.1:
        ton_amount = 0.1
    
    ton_link = f"ton://transfer/{TON_WALLET}?amount={int(ton_amount * 1e9)}&text={callback.from_user.id}"
    
    await state.update_data(ton_amount=ton_amount)
    
    show_agreement = not is_agreement_shown(callback.from_user.id)
    
    text = (
        f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
        f"👤 Получатель: @{username}\n"
        f"ℹ️ Номер заказа: #{order_number}\n"
        f"💰 Метод оплаты: Ton</code></pre>\n\n"
        f"❗ <b><u>Счёт активен в течении 3-х минут</u></b> ❗\n\n"
        f"<tg-emoji emoji-id='{EMOJI_IDS['waiting']}'>⏳</tg-emoji> <b>Ожидаем оплату...</b>"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Оплатить",
                url=ton_link
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data=f"cancel_ton_{purchase_id}"
            )]
        ]
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("payment.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=keyboard
    )
    await callback.answer()
    
    asyncio.create_task(auto_check_ton_payment(callback.message, purchase_id, state, ton_amount, order_number))

async def auto_check_ton_payment(message, purchase_id: int, state: FSMContext, ton_amount: float, order_number: str = None):
    for _ in range(36):
        await asyncio.sleep(5)
        
        purchase = get_purchase_by_id(purchase_id)
        if not purchase or purchase['status'] == 'completed':
            return
        
        payment_data = await ton_api.check_payment_by_comment(
            message.chat.id, 
            ton_amount,
            max_age_seconds=180
        )
        
        if payment_data:
            complete_purchase(purchase_id)
            
            if purchase['type'] == 'stars':
                success, result = await execute_stars_purchase(purchase_id)
                if not success:
                    logger.error(f"Failed to execute stars purchase: {result}")
            elif purchase['type'] == 'premium':
                success, result = await execute_premium_purchase(purchase_id)
                if not success:
                    logger.error(f"Failed to execute premium purchase: {result}")
            
            tx_hash = payment_data.get('hash', '')
            if tx_hash:
                update_purchase_invoice(purchase_id, tx_hash)
            
            data = await state.get_data()
            if not order_number:
                order_number = data.get('order_number', str(random.randint(10000, 99999)))
            
            user = get_user(message.chat.id)
            if user:
                username = user.get('username') or message.chat.username or str(message.chat.id)
            else:
                username = message.chat.username or str(message.chat.id)
            
            text = (
                f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
                f"👤 Получатель: @{username}\n"
                f"ℹ️ Номер заказа: #{order_number}\n"
                f"💰 Метод оплаты: Ton</code></pre>\n\n"
                f"<tg-emoji emoji-id='{EMOJI_IDS['processing']}'>🔁</tg-emoji> <b>Выполняем ваш заказ...</b>"
            )
            
            try:
                await message.edit_media(
                    media=InputMediaPhoto(
                        media=get_image("payment.jpg"),
                        caption=text,
                        parse_mode="HTML"
                    ),
                    reply_markup=None
                )
            except:
                pass
            
            await asyncio.sleep(3)
            
            success_text = (
                f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
                f"👤 Получатель: @{username}\n"
                f"ℹ️ Номер заказа: #{order_number}\n"
                f"💰 Метод оплаты: Ton</code></pre>\n\n"
                f"<tg-emoji emoji-id='{EMOJI_IDS['done']}'>✅</tg-emoji> <b>Ваш заказ успешно выполнен!</b>\n\n"
                f"<tg-emoji emoji-id='5444887644964159628'>💗</tg-emoji> <b>Благодарим вас за покупку!</b>"
            )
            
            review_url = f"{REVIEWS_WEBAPP_URL}?action=write&user_id={purchase['user_id']}&purchase_id={purchase_id}&order_number={order_number}"
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Оставить отзыв",
                        web_app=WebAppInfo(url=review_url),
                        icon_custom_emoji_id="5470060791883374114"
                    )],
                    [InlineKeyboardButton(
                        text="На главный экран",
                        callback_data="back_to_main",
                        icon_custom_emoji_id="5257963315258204021"
                    )]
                ]
            )
            
            try:
                await message.edit_media(
                    media=InputMediaPhoto(
                        media=get_image("payment.jpg"),
                        caption=success_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=keyboard
                )
            except:
                pass
            
            return
    
    purchase = get_purchase_by_id(purchase_id)
    if purchase and purchase['status'] != 'completed':
        data = await state.get_data()
        if not order_number:
            order_number = data.get('order_number', str(random.randint(10000, 99999)))
        
        user = get_user(message.chat.id)
        if user:
            username = user.get('username') or message.chat.username or str(message.chat.id)
        else:
            username = message.chat.username or str(message.chat.id)
        
        timeout_text = (
            f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
            f"👤 Получатель: @{username}\n"
            f"ℹ️ Номер заказа: #{order_number}\n"
            f"💰 Метод оплаты: Ton</code></pre>\n\n"
            f"❌ <b>Время оплаты истекло. Попробуйте снова.</b>"
        )
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="На главный экран",
                    callback_data="back_to_main",
                    icon_custom_emoji_id="5257963315258204021"
                )]
            ]
        )
        
        try:
            await message.edit_media(
                media=InputMediaPhoto(
                    media=get_image("payment.jpg"),
                    caption=timeout_text,
                    parse_mode="HTML"
                ),
                reply_markup=keyboard
            )
        except:
            pass

@router.callback_query(F.data.startswith("cancel_ton_"))
async def cancel_ton_payment(callback: CallbackQuery, state: FSMContext):
    purchase_id = int(callback.data.split("_")[2])
    await state.clear()
    await callback.answer("❌ Оплата отменена", show_alert=True)
    
    from keyboards.main_menu import get_main_menu_keyboard
    user_name = callback.from_user.first_name or "Гость"
    
    greeting_text = (
        f"<tg-emoji emoji-id='5472427507842032538'>👋</tg-emoji> "
        f"<b>{user_name}, добро пожаловать в DuckStars</b>\n\n"
        f"<tg-emoji emoji-id='5417969813609795944'>⭐️</tg-emoji> "
        f"<b>У нас Вы можете приобрести Telegram Stars и Telegram Premium на свой аккаунт за рубли</b>\n\n"
        f"<tg-emoji emoji-id='5472299818464321370'>🛍️</tg-emoji> "
        f"<b>Хороших покупок!</b>"
    )
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("welcome.jpg"),
            caption=greeting_text,
            parse_mode="HTML"
        ),
        reply_markup=get_main_menu_keyboard()
    )