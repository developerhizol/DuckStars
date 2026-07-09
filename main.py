# main.py
import asyncio
import logging
import os
import json
import sqlite3

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from aiohttp import web

from handlers import (
    start_router,
    stars_router,
    premium_router,
    gifts_router,
    profile_router,
    payment_router,
    back_router
)
from handlers.review_notification import check_and_send_review_notifications
from utils.database import init_db

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
dp.include_router(gifts_router)
dp.include_router(profile_router)
dp.include_router(payment_router)
dp.include_router(back_router)

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
        
        cursor.execute('''
            INSERT INTO reviews (purchase_id, user_id, username, type, item, stars_emoji, text, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (purchase_id, user_id, username, purchase['type'], purchase['item'], stars_emoji, text, rating))
        
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

async def main():
    asyncio.create_task(check_and_send_review_notifications(bot))
    
    app = web.Application()
    app.router.add_get('/api/reviews', handle_reviews)
    app.router.add_post('/api/submit_review', handle_submit_review)
    app.router.add_get('/', handle_serve_index)
    app.router.add_get('/public/{filename}', handle_serve_gif)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("API сервер запущен на порту 8080")
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())