from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp
import uuid
import asyncio
import os
import logging
import random

from utils.database import complete_purchase, get_purchase_by_id, get_user, update_purchase_invoice, get_db
from handlers.stars import execute_stars_purchase
from handlers.premium import execute_premium_purchase
from dotenv import load_dotenv

load_dotenv()

router = Router()
logger = logging.getLogger(__name__)

MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID")
SECRET_KEY = os.getenv("PLATEGA_SECRET_KEY")
API_URL = "https://app.platega.io/transaction/process"

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

@router.callback_query(F.data == "payment_sbp")
async def payment_sbp(callback: CallbackQuery, state: FSMContext):
    logger.info(f"payment_sbp called by user {callback.from_user.id}")
    
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
    await state.update_data(payment_method="sbp")
    
    loading_text = f"<tg-emoji emoji-id='{EMOJI_IDS['waiting']}'>⏳</tg-emoji> <b>Генерируем счёт для оплаты...</b>"
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("loading.jpg"),
            caption=loading_text,
            parse_mode="HTML"
        ),
        reply_markup=None
    )
    
    success, result = await create_sbp_payment(purchase, username)
    
    if not success:
        await callback.answer(f"❌ Ошибка создания платежа: {result}", show_alert=True)
        return
    
    transaction_id_from_api = result.get('transactionId')
    if transaction_id_from_api:
        update_purchase_invoice(purchase_id, transaction_id_from_api)
        await state.update_data(transaction_id_api=transaction_id_from_api)
    
    redirect_url = result.get('redirect')
    
    text = (
        f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
        f"👤 Получатель: @{username}\n"
        f"ℹ️ Номер заказа: #{order_number}\n"
        f"💰 Метод оплаты: СБП</code></pre>\n\n"
        f"<tg-emoji emoji-id='{EMOJI_IDS['waiting']}'>⏳</tg-emoji> <b>Ожидаем оплату...</b>"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Оплатить",
                url=redirect_url
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data=f"cancel_sbp_{purchase_id}"
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

async def create_sbp_payment(purchase, username: str):
    try:
        amount = purchase['amount']
        
        payload = {
            "paymentMethod": 2,
            "paymentDetails": {
                "amount": amount,
                "currency": "RUB"
            },
            "description": f"{purchase['item']} (DuckStars)",
            "return": "https://duckstars.bothost.tech/",
            "failedUrl": "https://duckstars.bothost.tech/",
            "payload": f"purchase_{purchase['id']}",
            "metadata": {
                "userId": str(purchase['user_id']),
                "userName": username,
                "orderNumber": purchase.get('order_number', '')
            }
        }
        
        headers = {
            "X-MerchantId": MERCHANT_ID,
            "X-Secret": SECRET_KEY,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                API_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    logger.info(f"SBP payment created: {data}")
                    return True, data
                else:
                    logger.error(f"SBP payment error: {data}")
                    return False, data.get('message', 'Неизвестная ошибка')
                    
    except Exception as e:
        logger.error(f"SBP payment exception: {e}")
        return False, str(e)

@router.callback_query(F.data.startswith("cancel_sbp_"))
async def cancel_sbp_payment(callback: CallbackQuery, state: FSMContext):
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

async def handle_sbp_webhook(request):
    from main import bot
    from aiohttp import web
    
    try:
        data = await request.json()
        logger.info(f"SBP webhook received: {data}")
        
        status = data.get('status')
        transaction_id = data.get('id')
        
        if status == "CONFIRMED" and transaction_id:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT id, user_id, order_number, type FROM purchases WHERE invoice_id = ?', (transaction_id,))
            purchase = cursor.fetchone()
            
            if purchase:
                complete_purchase(purchase['id'])
                logger.info(f"Purchase {purchase['id']} completed via SBP webhook")
                
                if purchase['type'] == 'stars':
                    success, result = await execute_stars_purchase(purchase['id'])
                    if not success:
                        logger.error(f"Failed to execute stars purchase: {result}")
                elif purchase['type'] == 'premium':
                    success, result = await execute_premium_purchase(purchase['id'])
                    if not success:
                        logger.error(f"Failed to execute premium purchase: {result}")
                
                await send_success_message(purchase['user_id'], purchase['id'], purchase.get('order_number', ''))
                
            conn.close()
        
        return web.json_response({"ok": True})
    except Exception as e:
        logger.error(f"Error processing SBP webhook: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def send_success_message(chat_id: int, purchase_id: int, order_number: str = None):
    from main import bot
    
    purchase = get_purchase_by_id(purchase_id)
    if not purchase:
        return
    
    if not order_number:
        order_number = purchase.get('order_number', str(random.randint(10000, 99999)))
    
    user = get_user(chat_id)
    if user:
        username = user.get('username') or "User"
    else:
        username = "User"
    
    processing_text = (
        f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
        f"👤 Получатель: @{username}\n"
        f"ℹ️ Номер заказа: #{order_number}\n"
        f"💰 Метод оплаты: СБП</code></pre>\n\n"
        f"<tg-emoji emoji-id='{EMOJI_IDS['processing']}'>🔁</tg-emoji> <b>Выполняем ваш заказ...</b>"
    )
    
    await bot.send_photo(
        chat_id=chat_id,
        photo=get_image("payment.jpg"),
        caption=processing_text,
        parse_mode="HTML"
    )
    
    await asyncio.sleep(3)
    
    success_text = (
        f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
        f"👤 Получатель: @{username}\n"
        f"ℹ️ Номер заказа: #{order_number}\n"
        f"💰 Метод оплаты: СБП</code></pre>\n\n"
        f"<tg-emoji emoji-id='{EMOJI_IDS['done']}'>✅</tg-emoji> <b>Ваш заказ успешно выполнен!</b>\n\n"
        f"<tg-emoji emoji-id='5444887644964159628'>💗</tg-emoji> <b>Благодарим вас за покупку!</b>"
    )
    
    review_url = f"{REVIEWS_WEBAPP_URL}?action=write&user_id={chat_id}&purchase_id={purchase_id}&order_number={order_number}"
    
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
    
    await bot.send_photo(
        chat_id=chat_id,
        photo=get_image("payment.jpg"),
        caption=success_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )