from flask import render_template, redirect, url_for, request, flash, session, jsonify, send_from_directory, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .app import app, db, login_manager
from .models import User, Chat, Message, RequestCounter
from datetime import datetime, date
import os
from .yandex_art import generate_image, YandexARTError
from .limits import check_request_limit, get_user_requests_today, cleanup_old_data, get_db_size_mb, REQUESTS_PER_DAY
from typing import Optional
import re
import logging

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        # Переход на последний чат пользователя
        last_chat = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).first()
        if last_chat:
            return redirect(url_for('chat', chat_id=last_chat.id))
        # Если чатов нет — создать новый
        chat = Chat()
        chat.user_id = current_user.id
        chat.name = 'Новый чат'
        db.session.add(chat)
        db.session.commit()
        return redirect(url_for('chat', chat_id=chat.id))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username: str = request.form['username']
        password: str = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Пользователь уже существует')
            return redirect(url_for('register'))
        user = User()
        user.username = username
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username: str = request.form['username']
        password: str = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('chat_list'))
        flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/chats')
@login_required
def chat_list():
    # Удаляем пустой чат, если он есть
    last_chat = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).first()
    if last_chat:
        has_messages = Message.query.filter_by(chat_id=last_chat.id).count() > 0
        if not has_messages:
            db.session.delete(last_chat)
            db.session.commit()
        else:
            return redirect(url_for('chat', chat_id=last_chat.id))
    # Если чатов нет — создать новый
    chat = Chat()
    chat.user_id = current_user.id
    chat.name = 'Новый чат'
    db.session.add(chat)
    db.session.commit()
    return redirect(url_for('chat', chat_id=chat.id))

@app.route('/chat/<int:chat_id>')
@login_required
def chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        flash('Нет доступа к этому чату')
        return redirect(url_for('chat_list'))
    messages = Message.query.filter_by(chat_id=chat_id).all()
    admin_login = os.getenv('ADMIN_LOGIN', 'admin')
    aspect_ratio = chat.aspect_ratio if hasattr(chat, 'aspect_ratio') and chat.aspect_ratio else '1:1'
    return render_template('chat.html', chat=chat, messages=messages, admin_login=admin_login, aspect_ratio=aspect_ratio)

def generate_chat_name(prompt: str) -> str:
    """Генерирует название чата из prompt"""
    # Очищаем prompt от лишних символов
    clean_prompt = re.sub(r'[^\w\sа-яёА-ЯЁ]', '', prompt)
    words = clean_prompt.split()
    
    if len(words) <= 3:
        return clean_prompt[:30] if len(clean_prompt) <= 30 else clean_prompt[:27] + "..."
    
    # Берем первые 3-4 слова
    name_words = words[:4]
    name = " ".join(name_words)
    
    if len(name) <= 30:
        return name
    
    # Обрезаем до 30 символов
    return name[:27] + "..."

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    prompt: str = request.form['prompt']
    chat_id: Optional[str] = request.form.get('chat_id')
    aspect = request.form.get('aspect_ratio', '1:1')
    aspect_map = {
        '1:1': (1, 1),
        '4:3': (4, 3),
        '3:4': (3, 4),
        '16:9': (16, 9),
        '9:16': (9, 16)
    }
    aspect_ratio = aspect_map.get(aspect, (1, 1))
    if not prompt.strip():
        return jsonify({'error': 'Пустой запрос'}), 400
    # Новый чат создаём только если у пользователя нет чатов вообще
    if not chat_id or not chat_id.isdigit():
        user_chats = Chat.query.filter_by(user_id=current_user.id).count()
        if user_chats == 0:
            chat_name = generate_chat_name(prompt)
            chat = Chat()
            chat.user_id = current_user.id
            chat.name = chat_name
            chat.aspect_ratio = aspect
            db.session.add(chat)
            db.session.commit()
            chat_id = str(chat.id)
        else:
            return jsonify({'error': 'Чат не выбран'}), 400
    else:
        chat = Chat.query.get(int(chat_id))
        if chat:
            chat.aspect_ratio = aspect
            # Меняем название чата сразу после первого запроса, если оно ещё стандартное
            if chat.name == 'Новый чат':
                chat.name = generate_chat_name(prompt)
            db.session.commit()
    if not check_request_limit(current_user.id):
        return jsonify({'error': f'Превышен лимит запросов ({REQUESTS_PER_DAY} в день)'}), 429
    # Очистка старых данных при необходимости
    cleanup_old_data()
    # Сохраняем сообщение в БД до генерации, чтобы получить msg.id
    msg = Message()
    msg.chat_id = int(chat_id)
    msg.user_id = current_user.id
    msg.prompt = prompt
    db.session.add(msg)
    db.session.commit()
    try:
        image_url: str = generate_image(prompt, aspect_ratio=aspect_ratio, user_id=current_user.id, msg_id=msg.id)
        if not image_url or not image_url.startswith('/images/'):
            logging.error(f'Некорректный image_url: {image_url}')
            db.session.delete(msg)
            db.session.commit()
            return jsonify({'error': 'Ошибка генерации изображения (файл не создан или недоступен)'}), 500
        abs_path = os.path.join("static", "img", image_url.split("/")[-1])
        if not os.path.exists(abs_path):
            logging.error(f'Файл изображения не найден: {abs_path}')
            db.session.delete(msg)
            db.session.commit()
            return jsonify({'error': 'Файл изображения не найден на сервере'}), 500
    except YandexARTError as e:
        db.session.delete(msg)
        db.session.commit()
        return jsonify({'error': str(e)}), 500
    msg.image_url = image_url
    db.session.commit()
    chat_name = chat.name if chat else None
    return jsonify({'image_url': image_url, 'chat_id': chat_id, 'chat_name': chat_name})

@app.route('/create_chat', methods=['POST'])
@login_required
def create_chat():
    # Удаляем пустой чат, если он есть
    last_chat = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).first()
    if last_chat:
        has_messages = Message.query.filter_by(chat_id=last_chat.id).count() > 0
        if not has_messages:
            db.session.delete(last_chat)
            db.session.commit()
    chat_name: str = request.form.get('chat_name', '').strip()
    if not chat_name:
        chat_name = 'Новый чат'
    chat = Chat()
    chat.user_id = current_user.id
    chat.name = chat_name
    db.session.add(chat)
    db.session.commit()
    # Если ajax-запрос, возвращаем chat_id
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'chat_id': chat.id})
    return redirect(url_for('chat', chat_id=chat.id))

@app.route('/stats')
@login_required
def user_stats():
    """Возвращает статистику пользователя"""
    requests_today = get_user_requests_today(current_user.id)
    db_size = get_db_size_mb()
    return jsonify({
        'requests_today': requests_today,
        'requests_limit': REQUESTS_PER_DAY,
        'db_size_mb': round(db_size, 2)
    })

@app.route('/admin')
@login_required
def admin_panel():
    """Админ-панель"""
    # Проверяем, является ли пользователь админом
    admin_login = os.getenv('ADMIN_LOGIN', 'admin')
    if current_user.username != admin_login:
        flash('Доступ запрещён')
        return redirect(url_for('chat_list'))
    # Получаем статистику
    total_users = User.query.count()
    total_chats = Chat.query.count()
    total_messages = Message.query.count()
    db_size = get_db_size_mb()
    requests_today = get_user_requests_today(current_user.id)
    stats = {
        'requests_today': requests_today,
        'requests_limit': REQUESTS_PER_DAY,
        'db_size_mb': round(db_size, 2)
    }
    # Получаем последние пользователи
    recent_users = User.query.order_by(User.registered_at.desc()).limit(10).all()
    # Получаем статистику запросов за сегодня
    today = date.today()
    today_requests = RequestCounter.query.filter_by(date=today).all()
    total_requests_today = sum(counter.count for counter in today_requests)
    # Получаем всех пользователей и чаты для таблиц
    users = User.query.order_by(User.registered_at.desc()).all()
    chats = Chat.query.order_by(Chat.created_at.desc()).all()
    return render_template('admin.html', 
                         stats=stats,
                         total_users=total_users,
                         total_chats=total_chats,
                         total_messages=total_messages,
                         db_size=round(db_size, 2),
                         recent_users=recent_users,
                         total_requests_today=total_requests_today,
                         users=users,
                         chats=chats)

@app.route('/admin/users')
@login_required
def admin_users():
    """Список всех пользователей"""
    admin_login = os.getenv('ADMIN_LOGIN', 'admin')
    if current_user.username != admin_login:
        flash('Доступ запрещён')
        return redirect(url_for('chat_list'))
    
    users = User.query.order_by(User.registered_at.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/cleanup', methods=['POST'])
@login_required
def admin_cleanup():
    """Принудительная очистка старых данных"""
    admin_login = os.getenv('ADMIN_LOGIN', 'admin')
    if current_user.username != admin_login:
        flash('Доступ запрещён')
        return redirect(url_for('admin_panel'))
    
    try:
        cleanup_old_data()
        flash('Очистка выполнена успешно')
    except Exception as e:
        flash(f'Ошибка при очистке: {str(e)}')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>')
@login_required
def admin_delete_user(user_id):
    admin_login = os.getenv('ADMIN_LOGIN', 'admin')
    if current_user.username != admin_login:
        flash('Доступ запрещён')
        return redirect(url_for('chat_list'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удалён')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_chat/<int:chat_id>')
@login_required
def admin_delete_chat(chat_id):
    admin_login = os.getenv('ADMIN_LOGIN', 'admin')
    if current_user.username != admin_login:
        flash('Доступ запрещён')
        return redirect(url_for('chat_list'))
    chat = Chat.query.get_or_404(chat_id)
    # Удаляем все сообщения чата
    Message.query.filter_by(chat_id=chat.id).delete()
    db.session.delete(chat)
    db.session.commit()
    flash('Чат удалён')
    return redirect(url_for('admin_panel'))

@app.route('/delete_empty_chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_empty_chat(chat_id):
    chat = Chat.query.get(chat_id)
    if chat and chat.user_id == current_user.id:
        has_messages = Message.query.filter_by(chat_id=chat.id).count() > 0
        if not has_messages:
            db.session.delete(chat)
            db.session.commit()
            return '', 204
    return '', 204

@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static']
    if not current_user.is_authenticated and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

@app.route('/images/<path:filename>')
def serve_image(filename):
    import os
    from flask import current_app, abort
    abs_dir = os.path.abspath('static/img')
    abs_file = os.path.join(abs_dir, filename)
    current_app.logger.info(f'Запрос на изображение: {filename}')
    current_app.logger.info(f'Абсолютный путь: {abs_file}')
    current_app.logger.info(f'Текущая рабочая директория: {os.getcwd()}')
    if not os.path.exists(abs_file):
        current_app.logger.error(f'Файл не найден: {abs_file}')
        abort(404)
    else:
        current_app.logger.info(f'Файл найден: {abs_file}')
    return send_file(abs_file, mimetype='image/jpeg')

@app.route('/chats/list')
@login_required
def chat_list_ajax():
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()
    return render_template('chat_list_partial.html', chats=chats)

@app.route('/delete_chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.user_id != current_user.id:
        return jsonify({'error': 'Нет доступа'}), 403
    # Удаляем все сообщения чата
    Message.query.filter_by(chat_id=chat.id).delete()
    db.session.delete(chat)
    db.session.commit()
    return jsonify({'success': True}) 