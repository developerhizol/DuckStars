# handlers/gifts.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
import aiohttp

from keyboards.gifts import (
    get_gifts_recipient_keyboard,
    get_gifts_friend_keyboard,
    get_gifts_anonymity_keyboard,
    get_gifts_list_keyboard,
    get_gifts_comment_keyboard,
    get_gifts_payment_keyboard
)
from utils.states import GiftsStates
from utils.database import add_purchase

router = Router()

GIFTS_IMAGE_URL = "https://keephere.ru/get/1NSVaq5WCe1/o/photo.jpg"
PAYMENT_IMAGE_URL = "https://keephere.ru/get/DNSVc06HK7h/o/photo.jpg"
HEART_EFFECT_ID = "5159385139981059251"

GIFT_EMOJIS = {
    "gift_tree": {"emoji": "🎄", "id": "5345935030143196497"},
    "gift_monkey": {"emoji": "🐒", "id": "5379850840691476775"},
    "gift_heart": {"emoji": "💝", "id": "5224628072619216265"},
    "gift_pinata": {"emoji": "🪅", "id": "5226661632259691727"},
    "gift_santa": {"emoji": "🎅", "id": "5289761157173775507"},
    "gift_cat": {"emoji": "😻", "id": "5317000922096769303"},
    "gift_bear": {"emoji": "🐻‍❄️", "id": "5359736160224586485"},
    "gift_ghost": {"emoji": "👻", "id": "5393309541620291208"},
    "gift_worker": {"emoji": "👷‍♂️", "id": "5447213743417105726"}
}

@router.callback_query(F.data == "buy_gifts")
async def buy_gifts(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiftsStates.choose_recipient)
    
    text = (
        f"<tg-emoji emoji-id='5970074171449808121'>🎁</tg-emoji> "
        f"<b>Покупка удаленных подарков</b>\n\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<i>Выберите получателя подарка:</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_recipient_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "gifts_self")
async def gifts_self(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiftsStates.choose_anonymity)
    await state.update_data(recipient=f"@{callback.from_user.username or callback.from_user.id}")
    
    text = (
        f"<b>Отправить подарок анонимно?</b>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_anonymity_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "gifts_friend")
async def gifts_friend(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiftsStates.choose_anonymity)
    
    text = (
        f"<b>Введите имя пользователя человека, которому хотите подарить подарок</b>"
    )
    
    await callback.message.edit_caption(
        caption=text,
        parse_mode="HTML"
    )
    await callback.message.edit_reply_markup(
        reply_markup=get_gifts_friend_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()

@router.message(GiftsStates.choose_anonymity)
async def gifts_username_input(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_message_id = data.get('bot_message_id')
    
    if not bot_message_id:
        await message.delete()
        await message.answer("Произошла ошибка, попробуйте снова")
        return
    
    if message.text and message.text.startswith('@'):
        username = message.text
        await message.delete()
        
        await state.update_data(recipient=username)
        
        text = (
            f"<b>Отправить подарок анонимно?</b>"
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.get(GIFTS_IMAGE_URL) as response:
                image_data = await response.read()
        
        await message.bot.edit_message_media(
            media=InputMediaPhoto(
                media=BufferedInputFile(image_data, filename="gifts.jpg"),
                caption=text,
                parse_mode="HTML"
            ),
            chat_id=message.chat.id,
            message_id=bot_message_id,
            reply_markup=get_gifts_anonymity_keyboard()
        )
        await state.update_data(bot_message_id=bot_message_id)
    else:
        await message.delete()
        await message.answer("<b>Пожалуйста, введите корректный @username</b>", parse_mode="HTML")

@router.callback_query(F.data.startswith("gifts_anon_"))
async def gifts_anonymity_select(callback: CallbackQuery, state: FSMContext):
    anonymity = "Да" if callback.data == "gifts_anon_yes" else "Нет"
    await state.update_data(anonymity=anonymity)
    await state.set_state(GiftsStates.choose_gift)
    
    data = await state.get_data()
    recipient = data.get('recipient', f"@{callback.from_user.username or callback.from_user.id}")
    
    gifts_list = " ".join([f"<tg-emoji emoji-id='{gift['id']}'>{gift['emoji']}</tg-emoji>" for gift in GIFT_EMOJIS.values()])
    
    text = (
        f"<tg-emoji emoji-id='5970074171449808121'>🎁</tg-emoji> "
        f"<b>Покупка удаленного подарка</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>{recipient}</b>\n"
        f"<tg-emoji emoji-id='5454339064096366207'>🥷</tg-emoji> "
        f"<b>Анонимная отправка:</b> <u>{anonymity}</u>\n\n"
        f"<b>Список удаленных подарков:</b>\n"
        f"{gifts_list}\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"Выберите подарок:"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_list_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("gift_"))
async def gifts_select(callback: CallbackQuery, state: FSMContext):
    gift_key = callback.data
    gift_data = GIFT_EMOJIS.get(gift_key)
    if not gift_data:
        await callback.answer("Подарок не найден", show_alert=True)
        return
    
    await state.update_data(gift=gift_key, gift_emoji=gift_data['emoji'], gift_emoji_id=gift_data['id'])
    await state.set_state(GiftsStates.choose_comment)
    
    text = (
        f"<tg-emoji emoji-id='5339536521009571338'>💬</tg-emoji> "
        f"<b>Введите комментарий к подарку</b>\n\n"
        f"<tg-emoji emoji-id='5231249426130935149'>🙏</tg-emoji> "
        f"<b>Внимание:</b> <i><u>не используйте премиум эмодзи, они заменятся на обычные!</u></i>\n"
        f"<b>Если вы не хотите добавлять комментарий, отправьте</b> <code>-</code>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_comment_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()

@router.message(GiftsStates.choose_comment)
async def gifts_comment_input(message: Message, state: FSMContext):
    data = await state.get_data()
    bot_message_id = data.get('bot_message_id')
    
    if not bot_message_id:
        await message.delete()
        await message.answer("Произошла ошибка, попробуйте снова", message_effect_id=HEART_EFFECT_ID)
        return
    
    comment = message.text
    if comment == "-":
        comment = ""
    await state.update_data(comment=comment)
    await state.set_state(GiftsStates.choose_payment)
    
    data = await state.get_data()
    gift_emoji_id = data.get('gift_emoji_id', '5345935030143196497')
    gift_emoji = data.get('gift_emoji', '🎄')
    
    purchase_id = add_purchase(
        user_id=message.from_user.id,
        type="gift",
        item=f"Удаленный подарок {gift_emoji}",
        amount=85,
        stars=85,
        recipient=data.get('recipient')
    )
    await state.update_data(purchase_id=purchase_id)
    
    await message.delete()
    
    text = (
        f"<blockquote><tg-emoji emoji-id='5312361253610475399'>🛒</tg-emoji> <b>Ваш товар:</b> подарок <tg-emoji emoji-id='{gift_emoji_id}'>{gift_emoji}</tg-emoji>\n"
        f"<tg-emoji emoji-id='5197434882321567830'>💵</tg-emoji> <b>Стоимость покупки:</b> 85 звёзд</blockquote>\n\n"
        f"<tg-emoji emoji-id='5470177992950946662'>👇</tg-emoji> <i>Пожалуйста, оплатите счёт ниже</i>"
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
            reply_markup=get_gifts_payment_keyboard()
        )
    except Exception as e:
        await message.answer("Произошла ошибка при обработке, попробуйте снова", message_effect_id=HEART_EFFECT_ID)

@router.callback_query(F.data == "gifts_pay_stars")
async def gifts_pay_stars(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏳ Оплата телеграм звездами в разработке...", show_alert=True)

@router.callback_query(F.data == "gifts_back")
async def gifts_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiftsStates.choose_recipient)
    
    text = (
        f"<tg-emoji emoji-id='5970074171449808121'>🎁</tg-emoji> "
        f"<b>Покупка удаленных подарков</b>\n\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<i>Выберите получателя подарка:</i>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_recipient_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "gifts_back_to_anon")
async def gifts_back_to_anon(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiftsStates.choose_anonymity)
    
    text = (
        f"<b>Отправить подарок анонимно?</b>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_anonymity_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "gifts_back_to_list")
async def gifts_back_to_list(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiftsStates.choose_gift)
    
    data = await state.get_data()
    recipient = data.get('recipient', f"@{callback.from_user.username or callback.from_user.id}")
    anonymity = data.get('anonymity', 'Да')
    
    gifts_list = " ".join([f"<tg-emoji emoji-id='{gift['id']}'>{gift['emoji']}</tg-emoji>" for gift in GIFT_EMOJIS.values()])
    
    text = (
        f"<tg-emoji emoji-id='5970074171449808121'>🎁</tg-emoji> "
        f"<b>Покупка удаленного подарка</b>\n"
        f"<tg-emoji emoji-id='5260399854500191689'>👤</tg-emoji> "
        f"<b>Получатель:</b> <b>{recipient}</b>\n"
        f"<tg-emoji emoji-id='5454339064096366207'>🥷</tg-emoji> "
        f"<b>Анонимная отправка:</b> <u>{anonymity}</u>\n\n"
        f"<b>Список удаленных подарков:</b>\n"
        f"{gifts_list}\n\n"
        f"<tg-emoji emoji-id='6024106569430472546'>📦</tg-emoji> "
        f"Выберите подарок:"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_list_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "gifts_back_to_comment")
async def gifts_back_to_comment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GiftsStates.choose_comment)
    
    text = (
        f"<tg-emoji emoji-id='5339536521009571338'>💬</tg-emoji> "
        f"<b>Введите комментарий к подарку</b>\n\n"
        f"<tg-emoji emoji-id='5231249426130935149'>🙏</tg-emoji> "
        f"<b>Внимание:</b> <i><u>не используйте премиум эмодзи, они заменятся на обычные!</u></i>\n"
        f"<b>Если вы не хотите добавлять комментарий, отправьте</b> <code>-</code>"
    )
    
    async with aiohttp.ClientSession() as session:
        async with session.get(GIFTS_IMAGE_URL) as response:
            image_data = await response.read()
    
    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=BufferedInputFile(image_data, filename="gifts.jpg"),
            caption=text,
            parse_mode="HTML"
        ),
        reply_markup=get_gifts_comment_keyboard()
    )
    await state.update_data(bot_message_id=callback.message.message_id)
    await callback.answer()