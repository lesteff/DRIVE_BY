[deepseek_bash_20260209_1dca85.sh](https://github.com/user-attachments/files/25184262/deepseek_bash_20260209_1dca85.sh)🚗 DRIVEBY - Car Rental Platform
Платформа для аренды автомобилей с полной интеграцией Telegram

✨ Ключевые особенности
🤖 Telegram-интеграция
Полное управление бронированиями через Telegram-бота

*Мгновенные уведомления о статусе аренд

*Безопасное подтверждение с уникальными кодами

*Автоматические напоминания о датах аренды


🎯 Умная система бронирования
⚡ Мгновенное бронирование в 3 клика

🛡️ Интеллектуальная проверка доступности автомобилей

📅 Защита от коллизий дат аренды

💰 Авторасчет стоимости с учетом скидок


🛠️ Технологический стек
Backend
Django 4.x 

PostgreSQL - надежная база данных

Frontend
Bootstrap 5 (Dark Theme) - адаптивная верстка

JavaScript ES6+ - интерактивные элементы

HTML5/CSS3 - семантическая верстка

Font Awesome - векторные иконки

Telegram Integration

python-telegram-bot - асинхронный бот

Django + async - интеграция синхронного и асинхронного кода

Webhook/Polling - гибкие методы обновлений

DevOps & Tools
Git - контроль версий

Docker - контейнеризация

GitHub Actions - CI/CD

pytest - автоматическое тестирование


📋 Основные функции
Для пользователей:
🔍 Поиск автомобилей с фильтрацией по параметрам

📅 Бронирование на любые даты

⭐ Система отзывов и рейтингов

👤 Личный кабинет с историей аренд

🤖 Управление через Telegram - подтверждение/отмена

Для администраторов:
🛠️ Панель управления Django Admin

📊 Аналитика бронирований

👥 Управление пользователями

🚗 Каталог автомобилей

💬 Модерация отзывов

🚀 Быстрый старт
Установка и запуск:

[Uploading dee# Клонирование репозитория
git clone https://github.com/lesteff/DRIVE_BY.git
cd DRIVE_BY

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск сервера
python manage.py runserver

# Запуск Telegram бота (в отдельном терминале)
python manage.py runbotpseek_bash_20260209_1dca85.sh…]()



Переменные окружения:
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost/driveby
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

🧪 Тестирование
# Запуск всех тестов
python manage.py test

# Запуск тестов с покрытием
coverage run --source='.' manage.py test
coverage report

# Тестирование форм
python manage.py test rental.tests.FormTests

# Тестирование представлений
python manage.py test rental.tests.ViewTests

🐳 Docker Deployment

# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/driveby

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=driveby
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password

  bot:
    build: .
    command: python manage.py runbot
    volumes:
      - .:/app
    depends_on:
      - web
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/driveby
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}

volumes:
  postgres_data:

