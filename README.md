# YandexART

Современное веб-приложение для генерации изображений с помощью YandexART API

---

## 🚀 Возможности
- Регистрация и авторизация пользователей
- Генерация изображений через YandexART API (IAM-токен)
- Многочаты с историей, автоудаление старых чатов
- Админ-панель, расширенная статистика, лимиты
- Современный UI в стиле Perplexity/ChatGPT, поддержка тёмной/светлой темы
- Скачивание изображений, адаптивность, быстрый UX

---

## 📦 Быстрый старт (Docker)

1. **Создайте файл `.env` в корне проекта:**
   ```
   SECRET_KEY=your_secret_key
   ADMIN_LOGIN=admin
   ADMIN_PASSWORD=admin_password
   YANDEX_OAUTH_TOKEN=ваш_яндекс_oauth_token
   YANDEX_FOLDER_ID=ваш_folder_id
   REQUESTS_PER_DAY=100
   DB_MAX_SIZE_MB=100
   IMG_MAX_SIZE_MB=300
   ```
2. **Соберите и запустите контейнер:**
   ```bash
   docker build -t yandexart .
   docker run -d -p 5000:5000 --env-file .env yandexart
   ```
3. **Откройте в браузере:**
   [http://localhost:5000](http://localhost:5000)

---

## 🛠️ Ручной запуск (локально)

### Windows
1. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements-prod.txt
   ```
3. Настройте `.env` (см. выше)
4. Инициализируйте БД:
   ```bash
   cd YandexART
   python create_db.py
   ```
5. Запустите приложение:
   ```bash
   python serve.py
   ```

### Linux/macOS
1. Создайте и активируйте виртуальное окружение:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements-prod.txt
   ```
3. Настройте `.env` (см. выше)
4. Инициализируйте БД:
   ```bash
   cd YandexART
   python create_db.py
   ```
5. Запустите приложение:
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
   ```

---

## 🚀 Деплой на GitHub

### 1. Подготовка репозитория
```bash
# Инициализируйте git (если еще не сделано)
git init
git add .
git commit -m "Initial commit"

# Создайте репозиторий на GitHub и добавьте remote
git remote add origin https://github.com/YOUR_USERNAME/YandexART.git
git branch -M main
git push -u origin main
```

### 2. Настройка GitHub Actions (опционально)
Создайте файл `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Server
on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /opt/yandexart
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo systemctl restart yandexart
```

---

## 🌐 Деплой на Ubuntu Server

### Автоматический деплой
1. **Подключитесь к серверу:**
   ```bash
   ssh user@your-server-ip
   ```

2. **Скачайте и запустите скрипт деплоя:**
   ```bash
   wget https://raw.githubusercontent.com/YOUR_USERNAME/YandexART/main/YandexART/deploy.sh
   chmod +x deploy.sh
   sudo ./deploy.sh
   ```

3. **Настройте переменные окружения:**
   ```bash
   sudo nano /opt/yandexart/.env
   ```

### Ручной деплой

#### 1. Подготовка сервера
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем зависимости
sudo apt install -y python3 python3-pip python3-venv nginx git

# Создаем пользователя
sudo useradd -m -s /bin/bash yandexart
sudo usermod -aG sudo yandexart
```

#### 2. Клонирование и настройка
```bash
# Клонируем репозиторий
sudo mkdir -p /opt/yandexart
sudo chown yandexart:yandexart /opt/yandexart
cd /opt/yandexart
sudo -u yandexart git clone https://github.com/YOUR_USERNAME/YandexART.git .

# Создаем виртуальное окружение
sudo -u yandexart python3 -m venv venv
sudo -u yandexart venv/bin/pip install -r requirements.txt
```

#### 3. Настройка переменных окружения
```bash
sudo -u yandexart nano .env
```
Содержимое `.env`:
```
SECRET_KEY=your-secret-key-here
YANDEX_ART_API_KEY=your-yandex-art-api-key
YANDEX_IAM_TOKEN=your-yandex-iam-token
ADMIN_LOGIN=admin
REQUESTS_PER_DAY=50
```

#### 4. Инициализация БД
```bash
sudo -u yandexart venv/bin/python create_db.py
```

#### 5. Настройка systemd
```bash
# Копируем сервис
sudo cp yandexart.service /etc/systemd/system/

# Включаем и запускаем
sudo systemctl daemon-reload
sudo systemctl enable yandexart
sudo systemctl start yandexart
```

#### 6. Настройка nginx
```bash
# Копируем конфигурацию
sudo cp nginx.conf /etc/nginx/sites-available/yandexart

# Включаем сайт
sudo ln -sf /etc/nginx/sites-available/yandexart /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Проверяем и перезапускаем
sudo nginx -t
sudo systemctl restart nginx
```

#### 7. Настройка firewall
```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
```

---

## ⚙️ Переменные окружения
- `SECRET_KEY` — секретный ключ Flask
- `ADMIN_LOGIN` — логин администратора
- `YANDEX_ART_API_KEY` — API ключ YandexART
- `YANDEX_IAM_TOKEN` — IAM токен для Yandex Cloud
- `REQUESTS_PER_DAY` — лимит генераций в сутки на пользователя

---

## 📁 Структура проекта
```
YandexART/
├── app.py              # Flask-приложение
├── models.py           # SQLAlchemy-модели
├── routes.py           # Основные маршруты
├── yandex_iam.py       # Работа с IAM-токеном
├── yandex_art.py       # Интеграция с YandexART API
├── limits.py           # Лимиты и очистка
├── create_db.py        # Инициализация БД
├── serve.py            # Production сервер (waitress)
├── templates/          # Jinja2-шаблоны (UI)
├── static/             # Статика (иконки, img/)
├── requirements.txt    # Зависимости для разработки
├── requirements-prod.txt # Зависимости для production
├── Dockerfile          # Docker-образ
├── docker-compose.yml  # Docker Compose
├── nginx.conf          # Конфигурация nginx
├── yandexart.service   # systemd сервис
├── deploy.sh           # Скрипт автоматического деплоя
├── .dockerignore       # Исключения для Docker
└── README.md           # Документация
```

---

## 🔧 Полезные команды

### Управление приложением
```bash
# Статус приложения
sudo systemctl status yandexart

# Перезапуск приложения
sudo systemctl restart yandexart

# Просмотр логов
sudo journalctl -u yandexart -f

# Проверка конфигурации nginx
sudo nginx -t

# Перезапуск nginx
sudo systemctl restart nginx
```

### Обновление приложения
```bash
cd /opt/yandexart
sudo -u yandexart git pull origin main
sudo -u yandexart venv/bin/pip install -r requirements.txt
sudo systemctl restart yandexart
```

---

## 📝 Советы по production
- Используйте HTTPS (Let's Encrypt)
- Настройте регулярные бэкапы БД
- Мониторьте логи и ресурсы сервера
- Используйте CDN для статических файлов
- Настройте rate limiting в nginx

---

## 👨‍💻 Авторы и поддержка
- Telegram: @your_nick
- Issues: github.com/yourrepo/issues

---

**YandexART — современный генератор изображений для ваших идей!** 