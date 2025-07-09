# 🚀 Инструкция по деплою YandexART

## 📋 Что подготовлено

✅ **Файлы для production:**
- `Dockerfile` - Docker образ с gunicorn
- `docker-compose.yml` - Docker Compose конфигурация
- `serve.py` - Production сервер для Windows
- `requirements-prod.txt` - Зависимости для production
- `nginx.conf` - Конфигурация nginx
- `yandexart.service` - systemd сервис
- `deploy.sh` - Автоматический скрипт деплоя
- `.github/workflows/deploy.yml` - GitHub Actions

✅ **Документация:**
- `README.md` - Обновлен с инструкциями
- `DEPLOY_CHECKLIST.md` - Чек-лист деплоя
- `env.example` - Пример переменных окружения

---

## 🎯 Быстрый деплой

### 1. Публикация на GitHub

```bash
# Проверяем статус
git status

# Добавляем все файлы
git add .

# Коммитим
git commit -m "Prepare for production deployment"

# Пушим на GitHub
git push origin main
```

### 2. Деплой на Ubuntu Server

```bash
# Подключаемся к серверу
ssh user@your-server-ip

# Скачиваем скрипт деплоя
wget https://raw.githubusercontent.com/YOUR_USERNAME/YandexART/main/YandexART/deploy.sh
chmod +x deploy.sh

# Запускаем автоматический деплой
sudo ./deploy.sh
```

### 3. Настройка переменных окружения

```bash
# Редактируем .env файл
sudo nano /opt/yandexart/.env
```

Содержимое `.env`:
```bash
SECRET_KEY=your-secret-key-here
YANDEX_ART_API_KEY=your-yandex-art-api-key
YANDEX_IAM_TOKEN=your-yandex-iam-token
ADMIN_LOGIN=admin
REQUESTS_PER_DAY=50
```

### 4. Проверка деплоя

```bash
# Статус приложения
sudo systemctl status yandexart

# Статус nginx
sudo systemctl status nginx

# Логи приложения
sudo journalctl -u yandexart -f
```

---

## 🔧 Альтернативные способы деплоя

### Docker деплой

```bash
# Сборка образа
docker build -t yandexart .

# Запуск контейнера
docker run -d -p 5000:5000 --env-file .env yandexart

# Или через docker-compose
docker-compose up -d
```

### Ручной деплой на Ubuntu

```bash
# 1. Подготовка системы
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx git

# 2. Создание пользователя
sudo useradd -m -s /bin/bash yandexart
sudo usermod -aG sudo yandexart

# 3. Клонирование репозитория
sudo mkdir -p /opt/yandexart
sudo chown yandexart:yandexart /opt/yandexart
cd /opt/yandexart
sudo -u yandexart git clone https://github.com/YOUR_USERNAME/YandexART.git .

# 4. Настройка окружения
sudo -u yandexart python3 -m venv venv
sudo -u yandexart venv/bin/pip install -r requirements.txt

# 5. Настройка .env
sudo -u yandexart nano .env

# 6. Инициализация БД
sudo -u yandexart venv/bin/python create_db.py

# 7. Настройка systemd
sudo cp yandexart.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable yandexart
sudo systemctl start yandexart

# 8. Настройка nginx
sudo cp nginx.conf /etc/nginx/sites-available/yandexart
sudo ln -sf /etc/nginx/sites-available/yandexart /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# 9. Настройка firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

---

## 🌐 Настройка домена и HTTPS

### 1. Настройка DNS
- Добавьте A-запись для вашего домена, указывающую на IP сервера

### 2. Установка Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 3. Получение SSL сертификата
```bash
sudo certbot --nginx -d your-domain.com
```

### 4. Автоматическое обновление
```bash
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📊 Мониторинг и бэкапы

### Мониторинг логов
```bash
# Логи приложения
sudo journalctl -u yandexart -f

# Логи nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Бэкап базы данных
```bash
# Создание бэкапа
sudo -u yandexart cp instance/yandexart.db /backup/yandexart_$(date +%Y%m%d_%H%M%S).db

# Автоматический бэкап (добавьте в crontab)
0 2 * * * sudo -u yandexart cp /opt/yandexart/instance/yandexart.db /backup/yandexart_$(date +\%Y\%m\%d).db
```

### Обновление приложения
```bash
cd /opt/yandexart
sudo -u yandexart git pull origin main
sudo -u yandexart venv/bin/pip install -r requirements.txt
sudo systemctl restart yandexart
```

---

## 🚨 Устранение проблем

### Приложение не запускается
```bash
# Проверка логов
sudo journalctl -u yandexart -f

# Проверка .env
sudo -u yandexart cat .env

# Проверка прав доступа
ls -la /opt/yandexart/
```

### nginx не работает
```bash
# Проверка конфигурации
sudo nginx -t

# Проверка логов
sudo tail -f /var/log/nginx/error.log

# Проверка портов
sudo netstat -tlnp
```

### Проблемы с базой данных
```bash
# Проверка прав
ls -la /opt/yandexart/instance/

# Пересоздание БД
sudo -u yandexart python create_db.py

# Проверка места
df -h
```

---

## ✅ Проверка готовности

- [ ] Приложение запущено и доступно
- [ ] nginx работает и проксирует запросы
- [ ] HTTPS настроен (если используется домен)
- [ ] Логи без ошибок
- [ ] Бэкапы настроены
- [ ] Мониторинг настроен

---

**🎉 Поздравляем! YandexART успешно развернут в production!** 