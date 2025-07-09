#!/usr/bin/env python3
"""
Production server для YandexART
Использует waitress для Windows или gunicorn для Linux
"""

import os
import sys

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    # Определяем порт из переменной окружения или используем 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    try:
        # Пробуем использовать waitress (для Windows)
        from waitress import serve
        print(f"🚀 Запуск YandexART через waitress на {host}:{port}")
        serve(app, host=host, port=port, threads=4)
    except ImportError:
        # Если waitress не установлен, используем встроенный сервер (только для разработки)
        print(f"⚠️  waitress не установлен, используем встроенный сервер (только для разработки)")
        print(f"🚀 Запуск YandexART на {host}:{port}")
        app.run(host=host, port=port, debug=False) 