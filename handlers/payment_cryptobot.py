# handlers/payment_cryptobot.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp
import uuid
import os

from utils.cryptobot import CryptoBotAPI
from utils.database import complete_purchase, get_purchase_by_id, update_purchase_invoice, get_user

router = Router()

CRYPTOBOT_TOKEN = "ВАШ_ТОКЕН_ОТ_CRYPTOBOT"
crypto_bot = CryptoBotAPI(CRYPTOBOT_TOKEN)
REVIEWS_WEBAPP_URL = "https://duckstars.bothost.tech/"
PAYMENT_IMAGE_URL = "https://keephere.ru/get/nNSgG_-OhXT/o/photo.jpg"

EMOJI_IDS = {
    "waiting": "5841359499146825803",
    "processing": "5841243255856960314",
    "done": "5444987348334965906",
    "home": "5257963315258204021"
}

@router.callback_query(F.data == "payment_ton")
async def payment_ton(callback: CallbackQuery, state: FSMContext):
    await process_cryptobot_payment(callback, state, "TON")

@router.callback_query(F.data == "payment_crypto")
async def payment_crypto(callback: CallbackQuery, state: FSMContext):
    await process_cryptobot_payment(callback, state, "USDT")

@router.callback_query(F.data == "payment_sbp")
async def payment_sbp(callback: CallbackQuery):
    await callback.answer("💳 СБП будет доступна после одобрения проекта в банке", show_alert=True)

@router.callback_query(F.data == "payment_card")
async def payment_card(callback: CallbackQuery):
    await callback.answer("💳 Оплата картой будет доступна после одобрения проекта в банке", show_alert=True)

async def process_cryptobot_payment(callback: CallbackQuery, state: FSMContext, asset: str):
    data = await state.get_data()
    purchase_id = data.get('purchase_id')
    
    if not purchase_id:
        await callback.answer("❌ Ошибка: покупка не найдена", show_alert=True)
        return
    
    purchase = get_purchase_by_id(purchase_id)
    if not purchase:
        await callback.answer("❌ Ошибка: покупка не найдена", show_alert=True)
        return
    
    user = get_user(callback.from_user.id)
    username = user.get('username') or callback.from_user.username or str(callback.from_user.id)
    
    transaction_id = str(uuid.uuid4())
    await state.update_data(transaction_id=transaction_id)
    
    usdt_amount = round(purchase['amount'] / 90, 2)
    if usdt_amount < 0.5:
        usdt_amount = 0.5
    
    invoice = await crypto_bot.create_invoice(
        amount=usdt_amount,
        asset=asset,
        description=f"{purchase['item']} (DuckStars)",
        paid_btn_url="https://t.me/DucksStarsRobot",
        hidden_message=f"purchase_{purchase_id}",
        test=True
    )
    
    if not invoice:
        await callback.answer("❌ Ошибка создания счета, попробуйте позже", show_alert=True)
        return
    
    update_purchase_invoice(purchase_id, invoice['invoice_id'])
    await state.update_data(invoice_id=invoice['invoice_id'])
    
    text = (
        f"✔️ <b>Вы выбрали покупку {purchase['item']}.</b>\n"
        f"👤 <b>Получатель:</b> @{username}\n"
        f"ℹ️ <b>Номер заказа:</b> <code>#{purchase_id}</code>\n"
        f"🆔 <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
        f"<i>Нажимая «Оплатить» вы соглашаетесь с нашей <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>политикой конфиденциальности</a> и <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>пользовательским соглашением</a>.</i>\n\n"
        f"<tg-emoji emoji-id='{EMOJI_IDS['waiting']}'>⏳</tg-emoji> <b>Ожидаем оплату...</b>"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💎 Оплатить {asset}",
                url=invoice['pay_url']
            )],
            [InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=f"cancel_payment_{purchase_id}"
            )]
        ]
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
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_payment_"))
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    purchase_id = int(callback.data.split("_")[2])
    await state.clear()
    await callback.message.delete()
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
    
    await callback.message.answer(
        greeting_text,
        parse_mode="HTML",
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
    
    status = await crypto_bot.check_invoice_status(purchase['invoice_id'])
    
    if status == "paid":
        complete_purchase(purchase_id)
        await state.clear()
        await callback.answer("✅ Оплата подтверждена!", show_alert=True)
        
        data = await state.get_data()
        transaction_id = data.get('transaction_id', '')
        
        user = get_user(callback.from_user.id)
        username = user.get('username') or callback.from_user.username or str(callback.from_user.id)
        
        text = (
            f"✔️ <b>Вы выбрали покупку {purchase['item']}.</b>\n"
            f"👤 <b>Получатель:</b> @{username}\n"
            f"ℹ️ <b>Номер заказа:</b> <code>#{purchase_id}</code>\n"
            f"🆔 <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
            f"<i>Нажимая «Оплатить» вы соглашаетесь с нашей <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>политикой конфиденциальности</a> и <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>пользовательским соглашением</a>.</i>\n\n"
            f"<tg-emoji emoji-id='{EMOJI_IDS['processing']}'>🔁</tg-emoji> <b>Выполняем ваш заказ...</b>"
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
            reply_markup=None
        )
        
        await asyncio.sleep(3)
        
        success_text = (
            f"✔️ <b>Вы выбрали покупку {purchase['item']}.</b>\n"
            f"👤 <b>Получатель:</b> @{username}\n"
            f"ℹ️ <b>Номер заказа:</b> <code>#{purchase_id}</code>\n"
            f"🆔 <b>ID транзакции:</b> <code>{transaction_id}</code>\n\n"
            f"<i>Нажимая «Оплатить» вы соглашаетесь с нашей <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>политикой конфиденциальности</a> и <a href='https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19'>пользовательским соглашением</a>.</i>\n\n"
            f"<tg-emoji emoji-id='{EMOJI_IDS['done']}'>✅</tg-emoji> <b>Ваш заказ успешно выполнен!</b>"
        )
        
        review_url = f"{REVIEWS_WEBAPP_URL}?action=write&user_id={purchase['user_id']}&purchase_id={purchase_id}"
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="✍️ Оставить отзыв",
                    web_app=WebAppInfo(url=review_url)
                )],
                [InlineKeyboardButton(
                    text="🏠 На главный экран",
                    callback_data="back_to_main",
                    icon_custom_emoji_id=EMOJI_IDS['home']
                )]
            ]
        )
        
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=BufferedInputFile(image_data, filename="payment.jpg"),
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