#!/bin/bash

# Скрипт деплоя YandexART на Ubuntu Server
# Использование: ./deploy-unix.sh

set -e

echo "🚀 Начинаем деплой YandexART..."

# Проверяем, что мы на Ubuntu
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Этот скрипт предназначен для Ubuntu Linux"
    exit 1
fi

# Обновляем систему
echo "📦 Обновляем систему..."
sudo apt update && sudo apt upgrade -y

# Устанавливаем необходимые пакеты
echo "📦 Устанавливаем зависимости..."
sudo apt install -y python3 python3-pip python3-venv nginx git

# Создаем пользователя для приложения
echo "👤 Создаем пользователя yandexart..."
sudo useradd -m -s /bin/bash yandexart || true
sudo usermod -aG sudo yandexart

# Создаем директорию для приложения
echo "📁 Создаем директорию приложения..."
sudo mkdir -p /opt/yandexart
sudo chown yandexart:yandexart /opt/yandexart

# Клонируем репозиторий (замените на ваш URL)
echo "📥 Клонируем репозиторий..."
cd /opt/yandexart
sudo -u yandexart git clone https://github.com/YOUR_USERNAME/YandexART.git . || true

# Создаем виртуальное окружение
echo "🐍 Создаем виртуальное окружение..."
sudo -u yandexart python3 -m venv venv
sudo -u yandexart venv/bin/pip install --upgrade pip
sudo -u yandexart venv/bin/pip install -r requirements.txt

# Создаем .env файл
echo "⚙️  Создаем .env файл..."
sudo -u yandexart tee .env > /dev/null << EOF
SECRET_KEY=your-secret-key-here
YANDEX_ART_API_KEY=your-yandex-art-api-key
YANDEX_IAM_TOKEN=your-yandex-iam-token
ADMIN_LOGIN=admin
REQUESTS_PER_DAY=50
EOF

# Создаем базу данных
echo "🗄️  Создаем базу данных..."
sudo -u yandexart venv/bin/python create_db.py

# Настраиваем systemd сервис
echo "🔧 Настраиваем systemd сервис..."
sudo cp yandexart.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable yandexart
sudo systemctl start yandexart

# Настраиваем nginx
echo "🌐 Настраиваем nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/yandexart
sudo ln -sf /etc/nginx/sites-available/yandexart /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Настраиваем firewall
echo "🔥 Настраиваем firewall..."
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

echo "✅ Деплой завершен!"
echo "🌐 Приложение доступно по адресу: http://your-server-ip"
echo "📋 Полезные команды:"
echo "   sudo systemctl status yandexart    # Статус приложения"
echo "   sudo systemctl restart yandexart   # Перезапуск приложения"
echo "   sudo journalctl -u yandexart -f    # Логи приложения"
echo "   sudo nginx -t                      # Проверка конфигурации nginx" 