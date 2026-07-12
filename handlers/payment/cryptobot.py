from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp
import uuid
import asyncio
import random
import os
import logging

from utils.cryptobot import CryptoBotAPI
from utils.database import complete_purchase, get_purchase_by_id, update_purchase_invoice, get_user, is_agreement_shown, mark_agreement_shown
from handlers.stars import execute_stars_purchase
from handlers.premium import execute_premium_purchase
from dotenv import load_dotenv

load_dotenv()

router = Router()
logger = logging.getLogger(__name__)

CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
crypto_bot = CryptoBotAPI(CRYPTOBOT_TOKEN)

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

@router.callback_query(F.data == "payment_crypto")
async def payment_crypto(callback: CallbackQuery, state: FSMContext):
    await process_cryptobot_payment(callback, state, "USDT")

async def get_crypto_price(asset: str = "USDT") -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://pay.crypt.bot/api/getExchangeRates",
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
        ) as response:
            data = await response.json()
            if data.get("ok"):
                for rate in data.get("result", []):
                    if rate.get("source") == asset and rate.get("target") == "RUB":
                        return float(rate.get("rate"))
    return 90.0

async def process_cryptobot_payment(callback: CallbackQuery, state: FSMContext, asset: str):
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
    
    loading_text = f"<tg-emoji emoji-id='{EMOJI_IDS['waiting']}'>⏳</tg-emoji> <b>Генерируем счёт для оплаты...</b>"
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=get_image("loading.jpg"),
            caption=loading_text,
            parse_mode="HTML"
        ),
        reply_markup=None
    )
    
    rate = await get_crypto_price(asset)
    crypto_amount = round(purchase['amount'] / rate, 2)
    if crypto_amount < 0.5:
        crypto_amount = 0.5
    
    invoice = await crypto_bot.create_invoice(
        amount=crypto_amount,
        asset=asset,
        description=f"{purchase['item']} (DuckStars)",
        paid_btn_url="https://t.me/DucksStarsRobot",
        hidden_message=None,
        test=True
    )
    
    if not invoice:
        await callback.answer("❌ Ошибка создания счета, попробуйте позже", show_alert=True)
        return
    
    invoice_id = invoice.get('invoice_id')
    if invoice_id:
        update_purchase_invoice(purchase_id, str(invoice_id))
        await state.update_data(invoice_id=invoice_id)
    
    show_agreement = not is_agreement_shown(callback.from_user.id)
    
    text = (
        f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
        f"👤 Получатель: @{username}\n"
        f"ℹ️ Номер заказа: #{order_number}\n"
        f"🆔 ID транзакции: {transaction_id}</code></pre>\n\n"
    )
    
    if show_agreement:
        text += (
            f"<i>Нажимая «Оплатить» вы соглашаетесь с нашей <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>политикой конфиденциальности</a> и <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>пользовательским соглашением</a>.</i>\n\n"
        )
        mark_agreement_shown(callback.from_user.id)
    
    text += f"<tg-emoji emoji-id='{EMOJI_IDS['waiting']}'>⏳</tg-emoji> <b>Ожидаем оплату...</b>"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Оплатить",
                url=invoice['pay_url']
            )],
            [InlineKeyboardButton(
                text="Отмена",
                callback_data=f"cancel_payment_{purchase_id}"
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

@router.callback_query(F.data.startswith("cancel_payment_"))
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
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

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment(callback: CallbackQuery, state: FSMContext):
    purchase_id = int(callback.data.split("_")[2])
    
    purchase = get_purchase_by_id(purchase_id)
    if not purchase:
        await callback.answer("❌ Покупка не найдена", show_alert=True)
        return
    
    if purchase['status'] == 'completed':
        await callback.answer("✅ Оплата уже подтверждена!", show_alert=True)
        return
    
    if not purchase.get('invoice_id'):
        await callback.answer("❌ Ошибка: нет данных о счете", show_alert=True)
        return
    
    status = await crypto_bot.check_invoice_status(int(purchase['invoice_id']))
    
    if status == "paid":
        complete_purchase(purchase_id)
        
        if purchase['type'] == 'stars':
            success, result = await execute_stars_purchase(purchase_id)
            if not success:
                logger.error(f"Failed to execute stars purchase: {result}")
        elif purchase['type'] == 'premium':
            success, result = await execute_premium_purchase(purchase_id)
            if not success:
                logger.error(f"Failed to execute premium purchase: {result}")
        
        await state.clear()
        await callback.answer("✅ Оплата подтверждена!", show_alert=True)
        
        data = await state.get_data()
        transaction_id = data.get('transaction_id', '')
        order_number = data.get('order_number', str(random.randint(10000, 99999)))
        
        user = get_user(callback.from_user.id)
        if user:
            username = user.get('username') or callback.from_user.username or str(callback.from_user.id)
        else:
            username = callback.from_user.username or str(callback.from_user.id)
        
        show_agreement = not is_agreement_shown(callback.from_user.id)
        
        text = (
            f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
            f"👤 Получатель: @{username}\n"
            f"ℹ️ Номер заказа: #{order_number}\n"
            f"🆔 ID транзакции: {transaction_id}</code></pre>\n\n"
        )
        
        if show_agreement:
            text += (
                f"<i>Нажимая «Оплатить» вы соглашаетесь с нашей <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>политикой конфиденциальности</a> и <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>пользовательским соглашением</a>.</i>\n\n"
            )
            mark_agreement_shown(callback.from_user.id)
        
        text += f"<tg-emoji emoji-id='{EMOJI_IDS['processing']}'>🔁</tg-emoji> <b>Выполняем ваш заказ...</b>"
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=get_image("payment.jpg"),
                caption=text,
                parse_mode="HTML"
            ),
            reply_markup=None
        )
        
        await asyncio.sleep(3)
        
        success_text = (
            f"<pre><code>✔️ Вы выбрали покупку {purchase['item']}.\n"
            f"👤 Получатель: @{username}\n"
            f"ℹ️ Номер заказа: #{order_number}\n"
            f"🆔 ID транзакции: {transaction_id}</code></pre>\n\n"
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
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=get_image("payment.jpg"),
                caption=success_text,
                parse_mode="HTML"
            ),
            reply_markup=keyboard
        )
        
    elif status == "pending":
        await callback.answer("⏳ Счет еще не оплачен. Попробуйте позже.", show_alert=True)
    elif status == "expired":
        await callback.answer("❌ Счет истек. Создайте новый заказ.", show_alert=True)
    else:
        await callback.answer("❌ Ошибка проверки статуса", show_alert=True)