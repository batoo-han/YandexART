import os
from datetime import datetime, date
from .db import db
from .models import RequestCounter, Chat, Message
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger('limits')

REQUESTS_PER_DAY = int(os.getenv('REQUESTS_PER_DAY', 100))
DB_MAX_SIZE_MB = int(os.getenv('DB_MAX_SIZE_MB', 100))

def check_request_limit(user_id: int) -> bool:
    """Проверяет лимит запросов пользователя за день"""
    today = date.today()
    counter = RequestCounter.query.filter_by(
        user_id=user_id, 
        date=today
    ).first()
    
    if not counter:
        counter = RequestCounter()
        counter.user_id = user_id
        counter.date = today
        counter.count = 0
        db.session.add(counter)
    
    if counter.count >= REQUESTS_PER_DAY:
        logger.warning(f'Пользователь {user_id} превысил лимит запросов')
        return False
    
    counter.count += 1
    db.session.commit()
    return True

def get_user_requests_today(user_id: int) -> int:
    """Возвращает количество запросов пользователя за сегодня"""
    today = date.today()
    counter = RequestCounter.query.filter_by(
        user_id=user_id, 
        date=today
    ).first()
    return counter.count if counter else 0

def cleanup_old_data():
    """Очищает старые чаты и сообщения при превышении размера БД"""
    try:
        # Получаем размер БД
        db_path = 'instance/db.sqlite3'
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            logger.info(f'Размер БД: {size_mb:.2f} МБ')
            
            if size_mb > DB_MAX_SIZE_MB:
                logger.warning(f'Размер БД превышает лимит {DB_MAX_SIZE_MB} МБ')
                
                # Удаляем старые чаты (сначала самые старые)
                old_chats = Chat.query.order_by(Chat.created_at.asc()).limit(10).all()
                for chat in old_chats:
                    # Удаляем все сообщения чата
                    Message.query.filter_by(chat_id=chat.id).delete()
                    # Удаляем сам чат
                    db.session.delete(chat)
                
                db.session.commit()
                logger.info(f'Удалено {len(old_chats)} старых чатов')
                
    except Exception as e:
        logger.error(f'Ошибка при очистке БД: {e}')

def get_db_size_mb() -> float:
    """Возвращает размер БД в МБ"""
    db_path = 'instance/db.sqlite3'
    if os.path.exists(db_path):
        return os.path.getsize(db_path) / (1024 * 1024)
    return 0.0 