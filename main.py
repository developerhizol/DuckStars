import asyncio
import logging
import os
import json
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from aiohttp import web

from handlers import (
    start_router,
    stars_router,
    premium_router,
    profile_router,
    back_router,
    cryptobot_router,
    ton_router,
    sbp_router
)
from handlers.payment.sbp import handle_sbp_webhook
from utils.database import init_db, get_db
from utils.cryptobot import CryptoBotAPI
from utils.fragapi import FragAPI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_PATH = "data/database.db"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

init_db()

dp.include_router(start_router)
dp.include_router(stars_router)
dp.include_router(premium_router)
dp.include_router(profile_router)
dp.include_router(cryptobot_router)
dp.include_router(ton_router)
dp.include_router(sbp_router)
dp.include_router(back_router)

CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
FRAGAPI_TOKEN = os.getenv("FRAGAPI_TOKEN")

crypto_bot = CryptoBotAPI(CRYPTOBOT_TOKEN)
frag_api = FragAPI(FRAGAPI_TOKEN)

async def handle_cryptobot_webhook(request):
    try:
        data = await request.json()
        logger.info(f"CryptoBot webhook received: {data}")
        
        if data.get("event") == "invoice_paid":
            invoice = data.get("payload", {})
            hidden_message = invoice.get("hidden_message", "")
            
            if hidden_message and hidden_message.startswith("purchase_"):
                purchase_id = int(hidden_message.split("_")[1])
                
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE purchases 
                    SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'pending'
                ''', (purchase_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Purchase {purchase_id} completed via CryptoBot webhook")
                    
                    cursor.execute('SELECT user_id FROM purchases WHERE id = ?', (purchase_id,))
                    purchase = cursor.fetchone()
                    
                    if purchase:
                        await bot.send_message(
                            purchase['user_id'],
                            "✅ Ваш платеж успешно подтвержден! Спасибо за покупку!"
                        )
                conn.close()
        
        return web.json_response({"ok": True})
    except Exception as e:
        logger.error(f"Error processing CryptoBot webhook: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def handle_reviews(request):
    tab = request.query.get('tab', 'all')
    page = int(request.query.get('page', 1))
    limit = int(request.query.get('limit', 5))
    offset = (page - 1) * limit
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM reviews'
    params = []
    if tab == 'positive':
        query += ' WHERE rating >= 4'
    elif tab == 'negative':
        query += ' WHERE rating <= 2'
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    reviews = cursor.fetchall()
    
    count_query = 'SELECT COUNT(*) as count FROM reviews'
    count_params = []
    if tab == 'positive':
        count_query += ' WHERE rating >= 4'
    elif tab == 'negative':
        count_query += ' WHERE rating <= 2'
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()
    
    cursor.execute('SELECT COUNT(*) as count FROM reviews')
    all_count = cursor.fetchone()
    cursor.execute('SELECT COUNT(*) as count FROM reviews WHERE rating >= 4')
    positive_count = cursor.fetchone()
    cursor.execute('SELECT COUNT(*) as count FROM reviews WHERE rating <= 2')
    negative_count = cursor.fetchone()
    
    conn.close()
    
    return web.json_response({
        'reviews': [dict(r) for r in reviews],
        'total_pages': (total['count'] + limit - 1) // limit if total else 1,
        'counts': {
            'all': all_count['count'] if all_count else 0,
            'positive': positive_count['count'] if positive_count else 0,
            'negative': negative_count['count'] if negative_count else 0
        }
    })

async def handle_submit_review(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        purchase_id = data.get('purchase_id')
        rating = data.get('rating', 5)
        text = data.get('text', '')
        order_number = data.get('order_number', '')
        
        if not user_id or not purchase_id:
            return web.json_response({'success': False, 'error': 'Missing user_id or purchase_id'})
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM purchases WHERE id = ?', (purchase_id,))
        purchase = cursor.fetchone()
        if not purchase:
            conn.close()
            return web.json_response({'success': False, 'error': 'Purchase not found'})
        
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        username = user['username'] if user else f"User{user_id}"
        
        stars_emoji = "⭐"
        if purchase['type'] == 'premium':
            stars_emoji = "💎"
        elif purchase['type'] == 'gift':
            stars_emoji = "🎁"
        
        if not order_number:
            order_number = purchase.get('order_number', '')
        
        cursor.execute('''
            INSERT INTO reviews (purchase_id, user_id, username, type, item, stars_emoji, text, rating, order_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (purchase_id, user_id, username, purchase['type'], purchase['item'], stars_emoji, text, rating, order_number))
        
        cursor.execute('UPDATE purchases SET review_given = 1 WHERE id = ?', (purchase_id,))
        conn.commit()
        conn.close()
        
        return web.json_response({'success': True})
    except Exception as e:
        logger.error(f"Error submitting review: {e}")
        return web.json_response({'success': False, 'error': str(e)})

async def handle_serve_index(request):
    try:
        with open('public/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except FileNotFoundError:
        return web.Response(text='File not found', status=404)

async def handle_serve_gif(request):
    filename = request.match_info.get('filename')
    filepath = os.path.join('public', filename)
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        return web.Response(body=content, content_type='image/gif')
    except FileNotFoundError:
        return web.Response(text='File not found', status=404)

async def handle_test_fragapi(request):
    try:
        me = await frag_api.get_me()
        if me:
            return web.json_response({
                "success": True,
                "balance": me.get('balance', 0),
                "user": me.get('username'),
                "id": me.get('id'),
                "firstName": me.get('firstName'),
                "lastName": me.get('lastName')
            })
        else:
            return web.json_response({
                "success": False,
                "error": "Failed to get FragAPI data"
            })
    except Exception as e:
        logger.error(f"Test FragAPI error: {e}")
        return web.json_response({
            "success": False,
            "error": str(e)
        })

async def main():
    app = web.Application()
    app.router.add_post('/webhook/cryptobot', handle_cryptobot_webhook)
    app.router.add_post('/webhook/sbp', handle_sbp_webhook)
    app.router.add_get('/api/reviews', handle_reviews)
    app.router.add_post('/api/submit_review', handle_submit_review)
    app.router.add_get('/', handle_serve_index)
    app.router.add_get('/public/{filename}', handle_serve_gif)
    app.router.add_get('/test/fragapi', handle_test_fragapi)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 7216)
    await site.start()
    logger.info("API сервер запущен на порту 7351")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
