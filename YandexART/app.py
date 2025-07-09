from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os
import logging
from werkzeug.security import generate_password_hash
from .db import db
from .models import User

"""
Инициализация Flask-приложения, базы данных и логирования.
"""

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
    ]
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)

def ensure_admin():
    """Создаёт администратора, если его нет в базе."""
    admin_login = os.getenv('ADMIN_LOGIN', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
    if not User.query.filter_by(username=admin_login).first():
        user = User()
        user.username = admin_login
        user.password_hash = generate_password_hash(admin_password)
        db.session.add(user)
        db.session.commit()

with app.app_context():
    db.create_all()
    ensure_admin()

def create_db():
    """Создаёт все таблицы в базе данных."""
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True)

from . import routes 