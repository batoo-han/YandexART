# 🚀 Чек-лист деплоя YandexART

## ✅ Подготовка к публикации на GitHub

### 1. Проверка файлов
- [ ] Все файлы добавлены в git
- [ ] `.env` файл добавлен в `.gitignore`
- [ ] `env.example` создан с примером переменных
- [ ] README.md обновлен с инструкциями
- [ ] Все секреты и ключи убраны из кода

### 2. Настройка репозитория
```bash
# Проверяем статус
git status

# Добавляем все файлы
git add .

# Коммитим изменения
git commit -m "Prepare for production deployment"

# Пушим на GitHub
git push origin main
```

## ✅ Деплой на Ubuntu Server

### 1. Подготовка сервера
- [ ] Ubuntu 20.04+ установлен
- [ ] SSH доступ настроен
- [ ] Пользователь с sudo правами создан

### 2. Автоматический деплой
```bash
# Подключаемся к серверу
ssh user@your-server-ip

# Скачиваем и запускаем скрипт
wget https://raw.githubusercontent.com/batoo-han/YandexART/master/YandexART/deploy-unix.sh
chmod +x deploy.sh
sudo ./deploy.sh
```

### 3. Ручной деплой
- [ ] Система обновлена (`sudo apt update && sudo apt upgrade`)
- [ ] Зависимости установлены (python3, nginx, git)
- [ ] Пользователь yandexart создан
- [ ] Репозиторий клонирован в `/opt/yandexart`
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены (`pip install -r requirements.txt`)
- [ ] `.env` файл настроен
- [ ] База данных инициализирована
- [ ] systemd сервис настроен
- [ ] nginx настроен
- [ ] firewall настроен

### 4. Проверка деплоя
- [ ] Приложение запущено (`sudo systemctl status yandexart`)
- [ ] nginx работает (`sudo systemctl status nginx`)
- [ ] Сайт доступен по HTTP
- [ ] Логи без ошибок (`sudo journalctl -u yandexart -f`)

## ✅ Настройка GitHub Actions (опционально)

### 1. Секреты в репозитории
- [ ] `HOST` - IP адрес сервера
- [ ] `USERNAME` - имя пользователя на сервере
- [ ] `KEY` - приватный SSH ключ

### 2. Проверка workflow
- [ ] Файл `.github/workflows/deploy.yml` создан
- [ ] При пуше в main происходит деплой
- [ ] Логи деплоя успешны

## ✅ Production настройки

### 1. Безопасность
- [ ] HTTPS настроен (Let's Encrypt)
- [ ] Firewall настроен
- [ ] SSH ключи настроены
- [ ] Пароли изменены

### 2. Мониторинг
- [ ] Логи настроены
- [ ] Бэкапы настроены
- [ ] Мониторинг ресурсов

### 3. Производительность
- [ ] nginx кэширование настроено
- [ ] gunicorn workers оптимизированы
- [ ] Статические файлы оптимизированы

## 🔧 Полезные команды

### Проверка статуса
```bash
# Статус приложения
sudo systemctl status yandexart

# Логи приложения
sudo journalctl -u yandexart -f

# Статус nginx
sudo systemctl status nginx

# Проверка конфигурации nginx
sudo nginx -t
```

### Обновление приложения
```bash
cd /opt/yandexart
sudo -u yandexart git pull origin main
sudo -u yandexart venv/bin/pip install -r requirements.txt
sudo systemctl restart yandexart
```

### Бэкап базы данных
```bash
sudo -u yandexart cp instance/yandexart.db /backup/yandexart_$(date +%Y%m%d_%H%M%S).db
```

## 🚨 Устранение проблем

### Приложение не запускается
1. Проверьте логи: `sudo journalctl -u yandexart -f`
2. Проверьте .env файл: `sudo -u yandexart cat .env`
3. Проверьте права доступа: `ls -la /opt/yandexart/`

### nginx не работает
1. Проверьте конфигурацию: `sudo nginx -t`
2. Проверьте логи: `sudo tail -f /var/log/nginx/error.log`
3. Проверьте порты: `sudo netstat -tlnp`

### Проблемы с базой данных
1. Проверьте права: `ls -la /opt/yandexart/instance/`
2. Пересоздайте БД: `sudo -u yandexart python create_db.py`
3. Проверьте свободное место: `df -h`

---

**✅ Готово к деплою!** 