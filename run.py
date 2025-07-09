#!/usr/bin/env python3
import sys
import os

# Добавляем путь к модулю YandexART
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'YandexART'))

from YandexART.app import app

if __name__ == '__main__':
    print("Запуск YandexART приложения...")
    print("Откройте браузер и перейдите по адресу: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000) 