import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import random

DB_PATH = "data/database.db"

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_spent REAL DEFAULT 0,
            total_purchases INTEGER DEFAULT 0,
            balance REAL DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            item TEXT,
            amount REAL,
            stars INTEGER,
            recipient TEXT,
            invoice_id TEXT DEFAULT '',
            order_number TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            review_given INTEGER DEFAULT 0,
            review_notification_sent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute("PRAGMA table_info(purchases)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'invoice_id' not in columns:
        cursor.execute('ALTER TABLE purchases ADD COLUMN invoice_id TEXT DEFAULT ""')
    if 'order_number' not in columns:
        cursor.execute('ALTER TABLE purchases ADD COLUMN order_number TEXT DEFAULT ""')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER,
            user_id INTEGER,
            username TEXT,
            type TEXT,
            item TEXT,
            stars_emoji TEXT,
            text TEXT,
            rating INTEGER DEFAULT 1,
            order_number TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (purchase_id) REFERENCES purchases (id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    cursor.execute("PRAGMA table_info(reviews)")
    columns_reviews = [col[1] for col in cursor.fetchall()]
    if 'order_number' not in columns_reviews:
        cursor.execute('ALTER TABLE reviews ADD COLUMN order_number TEXT DEFAULT ""')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temp_purchases (
            user_id INTEGER PRIMARY KEY,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agreement_shown (
            user_id INTEGER PRIMARY KEY,
            shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

def update_user(user_id: int, **kwargs):
    conn = get_db()
    cursor = conn.cursor()
    fields = []
    values = []
    for key, value in kwargs.items():
        fields.append(f"{key} = ?")
        values.append(value)
    values.append(user_id)
    cursor.execute(f'UPDATE users SET {", ".join(fields)} WHERE user_id = ?', values)
    conn.commit()
    conn.close()

def add_purchase(user_id: int, type: str, item: str, amount: float, stars: int = 0, recipient: str = None, order_number: str = None):
    conn = get_db()
    cursor = conn.cursor()
    if not order_number:
        order_number = str(random.randint(10000, 99999))
    cursor.execute('''
        INSERT INTO purchases (user_id, type, item, amount, stars, recipient, order_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, type, item, amount, stars, recipient, order_number))
    purchase_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return purchase_id

def complete_purchase(purchase_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE purchases 
        SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (purchase_id,))
    conn.commit()
    conn.close()

def get_user_purchases(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM purchases 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    purchases = cursor.fetchall()
    conn.close()
    return [dict(p) for p in purchases]

def get_user_stats(user_id: int) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total_purchases,
            COALESCE(SUM(amount), 0) as total_spent
        FROM purchases 
        WHERE user_id = ? AND status = 'completed'
    ''', (user_id,))
    stats = cursor.fetchone()
    conn.close()
    return dict(stats) if stats else {"total_purchases": 0, "total_spent": 0}

def save_temp_purchase(user_id: int, data: dict):
    import json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO temp_purchases (user_id, data)
        VALUES (?, ?)
    ''', (user_id, json.dumps(data)))
    conn.commit()
    conn.close()

def get_temp_purchase(user_id: int) -> Optional[dict]:
    import json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT data FROM temp_purchases WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return json.loads(result[0]) if result else None

def delete_temp_purchase(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM temp_purchases WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_review(purchase_id: int, user_id: int, username: str, type: str, item: str, stars_emoji: str, text: str, rating: int = 1, order_number: str = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reviews (purchase_id, user_id, username, type, item, stars_emoji, text, rating, order_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (purchase_id, user_id, username, type, item, stars_emoji, text, rating, order_number))
    review_id = cursor.lastrowid
    cursor.execute('UPDATE purchases SET review_given = 1 WHERE id = ?', (purchase_id,))
    conn.commit()
    conn.close()
    return review_id

def get_reviews(limit: int = 5, offset: int = 0, rating_type: str = None) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM reviews'
    params = []
    if rating_type == 'positive':
        query += ' WHERE rating >= 4'
    elif rating_type == 'negative':
        query += ' WHERE rating <= 2'
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    cursor.execute(query, params)
    reviews = cursor.fetchall()
    conn.close()
    return [dict(r) for r in reviews]

def get_reviews_count(rating_type: str = None) -> int:
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT COUNT(*) as count FROM reviews'
    params = []
    if rating_type == 'positive':
        query += ' WHERE rating >= 4'
    elif rating_type == 'negative':
        query += ' WHERE rating <= 2'
    cursor.execute(query, params)
    count = cursor.fetchone()
    conn.close()
    return count['count'] if count else 0

def get_purchase_by_id(purchase_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM purchases WHERE id = ?', (purchase_id,))
    purchase = cursor.fetchone()
    conn.close()
    return dict(purchase) if purchase else None

def get_user_completed_purchases(user_id: int) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM purchases 
        WHERE user_id = ? AND status = 'completed' AND review_given = 0
        ORDER BY created_at DESC
    ''', (user_id,))
    purchases = cursor.fetchall()
    conn.close()
    return [dict(p) for p in purchases]

def get_purchases_for_review_notification() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM purchases 
        WHERE status = 'completed' 
        AND review_given = 0 
        AND review_notification_sent = 0
        AND completed_at <= datetime('now', '-15 minutes')
        ORDER BY completed_at ASC
    ''')
    purchases = cursor.fetchall()
    conn.close()
    return [dict(p) for p in purchases]

def mark_review_notification_sent(purchase_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE purchases SET review_notification_sent = 1 WHERE id = ?', (purchase_id,))
    conn.commit()
    conn.close()

def update_purchase_invoice(purchase_id: int, invoice_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE purchases SET invoice_id = ? WHERE id = ?', (invoice_id, purchase_id))
    conn.commit()
    conn.close()

def is_agreement_shown(user_id: int) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM agreement_shown WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_agreement_shown(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO agreement_shown (user_id)
        VALUES (?)
    ''', (user_id,))
    conn.commit()
    conn.close()

def mark_purchase_completed_with_data(purchase_id: int, transaction_id: str = None, message_hash: str = None):
    conn = get_db()
    cursor = conn.cursor()
    if transaction_id:
        cursor.execute('''
            UPDATE purchases 
            SET status = 'completed', 
                completed_at = CURRENT_TIMESTAMP,
                invoice_id = ?
            WHERE id = ?
        ''', (transaction_id, purchase_id))
    else:
        cursor.execute('''
            UPDATE purchases 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (purchase_id,))
    conn.commit()
    conn.close()