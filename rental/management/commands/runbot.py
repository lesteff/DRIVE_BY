from django.core.management.base import BaseCommand
import os
import sys


class Command(BaseCommand):
    help = 'Запускает Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Запуск Telegram бота...')

        # Добавляем nest_asyncio в начале
        try:
            import nest_asyncio
            nest_asyncio.apply()
            self.stdout.write('✅ nest_asyncio применен')
        except ImportError:
            self.stdout.write(self.style.WARNING('⚠️ Установите: pip install nest_asyncio'))
            self.stdout.write('Пытаемся запустить без nest_asyncio...')

        # Настраиваем Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rent_car.settings')

        try:
            import django
            django.setup()
            self.stdout.write('✅ Django настроен')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Ошибка Django: {e}'))

        # Получаем токен
        token = os.getenv('TELEGRAM_BOT_TOKEN')

        if not token:
            try:
                from django.conf import settings
                token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            except:
                pass

        if not token:
            self.stdout.write(self.style.ERROR('❌ TELEGRAM_BOT_TOKEN не найден!'))
            self.stdout.write('💡 Используйте: TELEGRAM_BOT_TOKEN="токен" python manage.py runbot')
            return

        self.stdout.write(self.style.SUCCESS(f'✅ Токен: {token[:15]}...'))

        # Импортируем и запускаем бота
        try:
            # Пробуем новый файл
            from rental.bots.telegram_bot import run_bot
            run_bot()

        except ImportError:
            # Пробуем старый файл
            try:
                from rental.bots.telegram_bot import run_bot
                run_bot()
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))
                import traceback
                traceback.print_exc()