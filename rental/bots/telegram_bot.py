import os
import sys
import asyncio
import logging
import nest_asyncio
from asgiref.sync import sync_to_async

nest_asyncio.apply()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная инициализация Django
def init_django():
    """Инициализация Django один раз при запуске"""
    try:
        import django
        from django.conf import settings

        if not settings.configured:
            # Добавляем путь для импорта Django
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rent_car.settings')
            django.setup()
            logger.info("✅ Django инициализирован")
            return True
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации Django: {e}")
        return False

DJANGO_INITIALIZED = init_django()


class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        self.application = None

        if not DJANGO_INITIALIZED:
            logger.error("Django не инициализирован!")

    async def _check_django(self):
        """Проверка инициализации Django"""
        if not DJANGO_INITIALIZED:
            return False
        return True

    async def start(self, update, context):
        """Обработчик команды /start"""
        try:
            user = update.effective_user

            welcome_text = (
                f'👋 Привет, {user.first_name}!\n\n'
                f'Я бот для подтверждения аренды автомобилей DRIVEBY.\n\n'
                f'📋 Доступные команды:\n'
                f'/start - Начать работу\n'
                f'/help - Помощь\n'
                f'/link <код> - Привязать аккаунт\n'
                f'/my_rentals - Мои аренды\n'
                f'/confirm <код> - Подтвердить аренду\n'
                f'/cancel <код> - Отменить аренду\n'
                f'/debug - Диагностика\n\n'
                f'Для привязки аккаунта получите код на сайте.'
            )

            await update.message.reply_text(welcome_text)
            logger.info(f"Пользователь {user.id} запустил бота")

        except Exception as e:
            logger.error(f"Ошибка в команде start: {e}")
            await update.message.reply_text("❌ Произошла ошибка.")

    async def help_command(self, update, context):
        """Обработчик команды /help"""
        help_text = (
            '🤖 Помощь по командам:\n\n'
            '📌 /link <код> - Привязать Telegram к аккаунту DRIVEBY\n'
            '   Пример: /link 123456\n\n'
            '✅ /confirm <код> - Подтвердить аренду\n'
            '   Пример: /confirm ABC123\n\n'
            '❌ /cancel <код> - Отменить аренду\n'
            '   Пример: /cancel ABC123\n\n'
            '📋 /my_rentals - Показать мои аренды\n\n'
            '🔍 /debug - Диагностика системы\n\n'
            '📊 /status - Показать статус аккаунта\n\n'
            '🆘 /help - Показать это сообщение\n\n'
            '📊 /pending - Показать аренды ожидающие подтверждения'
        )
        await update.message.reply_text(help_text)

    @sync_to_async
    def _check_profile_sync(self, chat_id, username):
        """Синхронная функция для проверки профиля"""
        try:
            from rental.models import UserProfile
            from django.contrib.auth.models import User

            results = {}

            try:
                profile_by_id = UserProfile.objects.get(telegram_id=chat_id)
                results['by_telegram_id'] = {
                    'user': profile_by_id.user.username,
                    'profile_id': profile_by_id.id
                }
            except UserProfile.DoesNotExist:
                results['by_telegram_id'] = "Не найден"
            except Exception as e:
                results['by_telegram_id'] = f"Ошибка: {e}"

            if username:
                try:
                    django_user = User.objects.get(username=username)
                    try:
                        profile_by_user = UserProfile.objects.get(user=django_user)
                        results['by_username'] = {
                            'user': django_user.username,
                            'telegram_id': profile_by_user.telegram_id,
                            'profile_id': profile_by_user.id
                        }
                    except UserProfile.DoesNotExist:
                        results['by_username'] = "Профиль не найден"
                except User.DoesNotExist:
                    results['by_username'] = "Пользователь не найден"
                except Exception as e:
                    results['by_username'] = f"Ошибка: {e}"
            else:
                results['by_username'] = "Нет username в Telegram"

            profiles_with_my_id = list(UserProfile.objects.filter(
                telegram_id=chat_id
            ).values_list('user__username', flat=True))
            results['all_with_my_id'] = profiles_with_my_id

            all_users_count = User.objects.count()
            all_profiles_count = UserProfile.objects.count()
            results['counts'] = {
                'users': all_users_count,
                'profiles': all_profiles_count
            }

            return results

        except Exception as e:
            logger.error(f"Ошибка в _check_profile_sync: {e}")
            return None

    async def debug_command(self, update, context):
        try:
            chat_id = update.effective_chat.id
            user = update.effective_user

            debug_info = f"🔍 Отладочная информация:\n\n"
            debug_info += f"👤 Telegram пользователь:\n"
            debug_info += f"   ID: {user.id}\n"
            debug_info += f"   Username: @{user.username if user.username else 'нет'}\n"
            debug_info += f"   Имя: {user.first_name if user.first_name else 'нет'}\n"
            debug_info += f"   Фамилия: {user.last_name if user.last_name else 'нет'}\n"
            debug_info += f"   Chat ID: {chat_id}\n\n"

            # Проверяем Django
            if not await self._check_django():
                debug_info += "❌ Django не инициализирован\n"
                await update.message.reply_text(debug_info)
                return
            else:
                debug_info += "✅ Django инициализирован\n"

                try:
                    results = await self._check_profile_sync(chat_id, user.username)

                    if results:
                        debug_info += f"\n📊 Поиск профиля:\n"

                        if isinstance(results['by_telegram_id'], dict):
                            debug_info += f"✅ Найден по telegram_id:\n"
                            debug_info += f"   Пользователь: {results['by_telegram_id']['user']}\n"
                            debug_info += f"   ID профиля: {results['by_telegram_id']['profile_id']}\n"
                        else:
                            debug_info += f"❌ По telegram_id: {results['by_telegram_id']}\n"

                        debug_info += f"\n🔎 По username @{user.username if user.username else 'нет'}:\n"
                        if isinstance(results['by_username'], dict):
                            debug_info += f"✅ Найден:\n"
                            debug_info += f"   Пользователь: {results['by_username']['user']}\n"
                            debug_info += f"   Telegram ID в профиле: {results['by_username']['telegram_id']}\n"
                            debug_info += f"   ID профиля: {results['by_username']['profile_id']}\n"
                        else:
                            debug_info += f"❌ {results['by_username']}\n"

                        debug_info += f"\n👥 Все профили с telegram_id={chat_id}:\n"
                        if results['all_with_my_id']:
                            for username in results['all_with_my_id']:
                                debug_info += f"   • {username}\n"
                        else:
                            debug_info += f"   Нет профилей\n"

                        debug_info += f"\n📈 Статистика БД:\n"
                        debug_info += f"   Всего пользователей: {results['counts']['users']}\n"
                        debug_info += f"   Всего профилей: {results['counts']['profiles']}\n"
                    else:
                        debug_info += "\n❌ Не удалось получить данные профиля\n"

                except Exception as e:
                    debug_info += f"\n❌ Ошибка проверки БД: {e}\n"

            if len(debug_info) > 4000:
                parts = [debug_info[i:i+4000] for i in range(0, len(debug_info), 4000)]
                for part in parts:
                    await update.message.reply_text(part)
            else:
                await update.message.reply_text(debug_info)

        except Exception as e:
            logger.error(f"Ошибка в debug_command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Ошибка отладки: {e}")

    @sync_to_async
    def _get_user_rentals_sync(self, chat_id, username):
        """Синхронная функция для получения аренд пользователя"""
        try:
            from rental.models import UserProfile, Rental
            from django.contrib.auth.models import User

            try:
                profile = UserProfile.objects.get(telegram_id=chat_id)
                found_user = profile.user
                rentals = list(Rental.objects.filter(user=found_user)
                               .select_related('car')
                               .prefetch_related('telegram_confirmation')
                               .order_by('-created_at')[:10])
                return found_user, rentals, "found_by_telegram_id"
            except UserProfile.DoesNotExist:
                pass

            if username:
                try:
                    found_user = User.objects.get(username=username)
                    rentals = list(Rental.objects.filter(user=found_user)
                                   .select_related('car')
                                   .prefetch_related('telegram_confirmation')
                                   .order_by('-created_at')[:10])
                    return found_user, rentals, "found_by_username"
                except User.DoesNotExist:
                    pass

            return None, [], "not_found"

        except Exception as e:
            logger.error(f"Ошибка в _get_user_rentals_sync: {e}")
            return None, [], "error"

    async def my_rentals(self, update, context):
        """Показать аренды пользователя - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            chat_id = update.effective_chat.id
            user = update.effective_user

            # Проверяем Django
            if not await self._check_django():
                await update.message.reply_text("❌ Системная ошибка. Попробуйте позже.")
                return

            found_user, rentals_list, found_by = await self._get_user_rentals_sync(chat_id, user.username)

            if found_user is None:
                response = (
                    '❌ Не удалось найти ваш аккаунт.\n\n'
                    'Возможные причины:\n'
                    '1. Вы еще не привязали Telegram к аккаунту на сайте\n'
                    '2. Ваш Telegram ID отличается от указанного в профиле\n\n'
                    '💡 Решение:\n'
                    '1. Зайдите на сайт DRIVEBY\n'
                    '2. В личном кабинете привяжите Telegram\n'
                    '3. Используйте код привязки: /link <код>\n\n'
                    '📊 Для диагностики используйте /debug'
                )
                await update.message.reply_text(response)
                return

            logger.info(
                f"Найден пользователь: {found_user.username} (метод: {found_by}), аренд: {len(rentals_list)}")

            if rentals_list:
                message = f'📋 Аренды пользователя {found_user.username}:\n\n'

                for rental in rentals_list:
                    if hasattr(rental, 'car') and rental.car:
                        car_info = f"{rental.car.brand} {rental.car.model}"
                    else:
                        car_info = "Автомобиль"

                    # Статус с иконками
                    status_icons = {
                        'pending': '⏳',
                        'active': '🚗',
                        'completed': '✅',
                        'cancelled': '❌'
                    }
                    status_icon = status_icons.get(rental.status, '📋')

                    start_date = rental.start_date.strftime('%d.%m.%Y')
                    end_date = rental.end_date.strftime('%d.%m.%Y')

                    message += (
                        f'{status_icon} {car_info}\n'
                        f'📅 {start_date} - {end_date}\n'
                        f'💰 {rental.total_price} BYN\n'
                        f'📊 Статус: {rental.get_status_display()}\n'
                        f'🆔 #{rental.id}\n'
                    )

                    if rental.status == 'pending':
                        try:
                            if hasattr(rental, 'telegram_confirmation') and rental.telegram_confirmation:
                                if rental.telegram_confirmation.status == 'pending':
                                    message += f'🔐 Код для подтверждения: {rental.telegram_confirmation.confirmation_code}\n'
                        except Exception as e:
                            logger.error(f"Ошибка проверки подтверждения: {e}")

                    message += '─' * 30 + '\n'

                if len(message) > 4000:
                    parts = [message[i:i + 4000] for i in range(0, len(message), 4000)]
                    for part in parts:
                        await update.message.reply_text(part)
                else:
                    await update.message.reply_text(message)

            else:
                await update.message.reply_text(
                    f'📭 У пользователя {found_user.username} пока нет аренд.\n\n'
                    'Перейдите на сайт DRIVEBY, чтобы выбрать автомобиль!'
                )

        except Exception as e:
            logger.error(f"Общая ошибка в my_rentals: {e}", exc_info=True)
            await update.message.reply_text(
                '❌ Ошибка при получении списка аренд.\n'
                f'Детали: {str(e)[:200]}\n\n'
                'Попробуйте позже или используйте /debug для диагностики.'
            )

    @sync_to_async
    def _link_account_sync(self, chat_id, username, first_name, last_name):
        """Синхронная функция для привязки аккаунта"""
        try:
            from rental.models import UserProfile
            from django.contrib.auth.models import User

            user_username = username or f"tg_{chat_id}"

            try:
                django_user = User.objects.get(username=user_username)
            except User.DoesNotExist:
                django_user = User.objects.create_user(
                    username=user_username,
                    email=f'{user_username}@driveby.rent',
                    first_name=first_name or 'Пользователь',
                    last_name=last_name or ''
                )

            profile, created = UserProfile.objects.get_or_create(
                user=django_user,
                defaults={'telegram_id': chat_id}
            )

            if not created:
                profile.telegram_id = chat_id
                profile.save()

            return django_user, profile, created

        except Exception as e:
            logger.error(f"Ошибка в _link_account_sync: {e}")
            raise

    async def link_account(self, update, context):
        """Привязка Telegram к существующему аккаунту DRIVEBY"""
        try:
            chat_id = update.effective_chat.id
            user = update.effective_user
            args = context.args

            if not args:
                await update.message.reply_text(
                    '❌ Пожалуйста, укажите код привязки.\n'
                    'Пример: /link 123456\n\n'
                    '💡 Как получить код?\n'
                    '1. Зайдите на сайт DRIVEBY\n'
                    '2. В личном кабинете найдите раздел "Telegram"\n'
                    '3. Скопируйте код привязки'
                )
                return

            link_code = args[0]

            if not await self._check_django():
                await update.message.reply_text("❌ Системная ошибка. Попробуйте позже.")
                return

            try:
                django_user, profile, created = await self._link_account_sync(
                    chat_id, user.username, user.first_name, user.last_name
                )

                logger.info(f"Привязка: user={django_user.username}, telegram_id={chat_id}, code={link_code}")

                response_text = (
                    f'✅ Аккаунт успешно привязан!\n\n'
                    f'👤 Пользователь: {django_user.username}\n'
                    f'📱 Telegram ID: {chat_id}\n'
                    f'🔑 Использован код: {link_code}\n\n'
                    f'Теперь вы можете:\n'
                    f'• Просматривать аренды (/my_rentals)\n'
                    f'• Подтверждать бронирования (/confirm)\n'
                    f'• Получать уведомления'
                )

                await update.message.reply_text(response_text)

            except Exception as e:
                logger.error(f"Ошибка привязки аккаунта: {e}", exc_info=True)
                await update.message.reply_text(
                    '❌ Ошибка при привязке аккаунта.\n'
                    'Попробуйте позже или обратитесь в поддержку.'
                )

        except Exception as e:
            logger.error(f"Общая ошибка в link_account: {e}", exc_info=True)
            await update.message.reply_text('❌ Произошла ошибка. Попробуйте позже.')

    @sync_to_async
    def _confirm_rental_sync(self, confirmation_code, chat_id):
        """Синхронная функция для подтверждения аренды"""
        try:
            from rental.models import TelegramConfirmation
            from django.utils import timezone

            # Используем select_related для загрузки связанных объектов
            confirmation = TelegramConfirmation.objects.select_related(
                'rental',
                'rental__car',
                'user'
            ).get(
                confirmation_code=confirmation_code,
                status='pending'
            )

            # Проверка срока действия
            if confirmation.expires_at and confirmation.expires_at < timezone.now():
                confirmation.status = 'expired'
                confirmation.save()
                return None, "Код подтверждения просрочен."

            # Проверка chat_id
            if confirmation.chat_id and str(confirmation.chat_id) != str(chat_id):
                return None, "Этот код подтверждения предназначен другому пользователю."

            # Устанавливаем chat_id если его нет
            if not confirmation.chat_id:
                confirmation.chat_id = chat_id

            # Подтверждаем
            confirmation.status = 'confirmed'
            confirmation.save()

            # Обновляем аренду
            rental = confirmation.rental
            rental.status = 'active'
            rental.save()

            # Возвращаем аренду с автомобилем
            return rental, None

        except TelegramConfirmation.DoesNotExist:
            return None, "Код подтверждения не найден."
        except Exception as e:
            logger.error(f"Ошибка в _confirm_rental_sync: {e}")
            return None, f"Внутренняя ошибка: {str(e)}"

    async def confirm_rental(self, update, context):
        """Подтверждение аренды"""
        try:
            chat_id = update.effective_chat.id
            args = context.args

            if not args:
                await update.message.reply_text(
                    '❌ Пожалуйста, укажите код подтверждения.\n'
                    'Пример: /confirm ABC123\n\n'
                    '💡 Где взять код?\n'
                    'Код приходит в уведомлении о новой аренде'
                )
                return

            confirmation_code = args[0].upper()

            if not await self._check_django():
                await update.message.reply_text("❌ Системная ошибка. Попробуйте позже.")
                return

            rental, error = await self._confirm_rental_sync(confirmation_code, chat_id)

            if error:
                await update.message.reply_text(f'❌ {error}')
                return

            # Формируем ответ
            car_info = f"{rental.car.brand} {rental.car.model}" if rental.car else "автомобиль"
            start_date = rental.start_date.strftime('%d.%m.%Y')
            end_date = rental.end_date.strftime('%d.%m.%Y')

            response_text = (
                f'✅ Аренда успешно подтверждена!\n\n'
                f'🚗 {car_info}\n'
                f'📅 {start_date} - {end_date}\n'
                f'💰 {rental.total_price} BYN\n'
                f'🆔 Номер аренды: #{rental.id}\n\n'
                f'Приятной поездки! 🚀'
            )

            await update.message.reply_text(response_text)
            logger.info(f"Аренда {rental.id} подтверждена кодом {confirmation_code}")

        except Exception as e:
            logger.error(f"Ошибка подтверждения: {e}", exc_info=True)
            await update.message.reply_text(
                '❌ Ошибка при подтверждении аренды.\n'
                'Проверьте код и попробуйте снова.'
            )

    @sync_to_async
    def _cancel_rental_sync(self, confirmation_code, chat_id):
        """Синхронная функция для отмены аренды"""
        try:
            from rental.models import TelegramConfirmation, UserProfile
            from django.utils import timezone

            confirmation = TelegramConfirmation.objects.select_related(
                'rental',
                'rental__car',
                'user'
            ).get(
                confirmation_code=confirmation_code
            )

            # Проверка прав доступа
            if confirmation.chat_id and str(confirmation.chat_id) != str(chat_id):
                try:
                    profile = UserProfile.objects.get(telegram_id=chat_id)
                    if confirmation.user != profile.user:
                        return {
                            'success': False,
                            'message': '❌ У вас нет доступа к этой аренде.\n'
                                       'Этот код подтверждения принадлежит другому пользователю.',
                            'rental': None
                        }
                except UserProfile.DoesNotExist:
                    return {
                        'success': False,
                        'message': '❌ Ваш аккаунт не найден в системе.',
                        'rental': None
                    }

            # Проверка статуса
            if confirmation.status != 'pending':
                if confirmation.status == 'confirmed':
                    return {
                        'success': False,
                        'message': '❌ Эта аренда уже подтверждена и не может быть отменена через бота.\n'
                                   'Для отмены подтвержденной аренды свяжитесь с поддержкой.',
                        'rental': confirmation.rental
                    }
                elif confirmation.status == 'rejected':
                    return {
                        'success': False,
                        'message': '❌ Эта аренда уже была отменена ранее.',
                        'rental': confirmation.rental
                    }
                elif confirmation.status == 'expired':
                    return {
                        'success': False,
                        'message': '❌ Срок действия кода подтверждения истек.',
                        'rental': confirmation.rental
                    }

            # Проверка срока действия
            if confirmation.expires_at and confirmation.expires_at < timezone.now():
                confirmation.status = 'expired'
                confirmation.save()
                return {
                    'success': False,
                    'message': '❌ Срок действия кода подтверждения истек.',
                    'rental': confirmation.rental
                }

            # Отменяем
            confirmation.status = 'rejected'
            confirmation.save()

            rental = confirmation.rental
            rental.status = 'cancelled'
            rental.save()

            return {
                'success': True,
                'message': f'✅ Аренда #{rental.id} успешно отменена!',
                'rental': rental
            }

        except TelegramConfirmation.DoesNotExist:
            return {
                'success': False,
                'message': '❌ Код подтверждения не найден.\n'
                           'Проверьте правильность кода и попробуйте снова.',
                'rental': None
            }
        except Exception as e:
            logger.error(f"Ошибка в _cancel_rental_sync: {e}")
            return {
                'success': False,
                'message': f'❌ Внутренняя ошибка: {str(e)}',
                'rental': None
            }

    async def cancel_rental(self, update, context):
        """Отмена аренды"""
        try:
            chat_id = update.effective_chat.id
            user = update.effective_user
            args = context.args

            if not args:
                await update.message.reply_text(
                    '❌ Пожалуйста, укажите код подтверждения.\n'
                    'Пример: /cancel ABC123\n\n'
                    '💡 *Где взять код?*\n'
                    'Код отображается в /my_rentals для аренд со статусом "Ожидает подтверждения"\n\n'
                    '⚠️ *Внимание:* Отмена аренды может облагаться штрафом согласно правилам аренды.',
                    parse_mode='Markdown'
                )
                return

            confirmation_code = args[0].upper()

            if not await self._check_django():
                await update.message.reply_text("❌ Системная ошибка. Попробуйте позже.")
                return

            result = await self._cancel_rental_sync(confirmation_code, chat_id)

            if not result['success']:
                await update.message.reply_text(result['message'])
                return

            rental = result['rental']

            # Формируем ответ
            car_info = f"{rental.car.brand} {rental.car.model}" if rental.car else "автомобиль"

            response_text = (
                f'{result["message"]}\n\n'
                f'📋 *Детали отмененной аренды:*\n'
                f'🚗 {car_info}\n'
                f'📅 {rental.start_date} - {rental.end_date}\n'
                f'💰 {rental.total_price} BYN\n'
                f'🆔 Номер аренды: #{rental.id}\n\n'
                f'💡 *Что дальше?*\n'
                f'• Деньги будут возвращены в течение 3-5 рабочих дней\n'
                f'• Проверьте ваш баланс на сайте\n'
                f'• Если у вас есть вопросы, свяжитесь с поддержкой\n\n'
                f'Спасибо, что пользуетесь DRIVEBY!'
            )

            await update.message.reply_text(response_text, parse_mode='Markdown')
            logger.info(f"✅ Аренда {rental.id} отменена пользователем {chat_id} с кодом {confirmation_code}")

        except Exception as e:
            logger.error(f"❌ Ошибка отмены аренды: {e}", exc_info=True)
            await update.message.reply_text(
                '❌ Произошла ошибка при отмене аренды.\n'
                'Пожалуйста, попробуйте позже или свяжитесь с поддержкой.'
            )

    @sync_to_async
    def _get_user_status_sync(self, chat_id):
        """Синхронная функция для получения статуса пользователя"""
        try:
            from rental.models import UserProfile, Rental

            try:
                profile = UserProfile.objects.get(telegram_id=chat_id)
                user = profile.user

                # Статистика
                total_rentals = Rental.objects.filter(user=user).count()
                active_rentals = Rental.objects.filter(user=user, status='active').count()
                pending_rentals = Rental.objects.filter(user=user, status='pending').count()

                return user, total_rentals, active_rentals, pending_rentals
            except UserProfile.DoesNotExist:
                return None, 0, 0, 0

        except Exception as e:
            logger.error(f"Ошибка в _get_user_status_sync: {e}")
            return None, 0, 0, 0

    async def status_command(self, update, context):
        """Показать статус пользователя"""
        try:
            chat_id = update.effective_chat.id

            if not await self._check_django():
                await update.message.reply_text("❌ Системная ошибка.")
                return

            user, total, active, pending = await self._get_user_status_sync(chat_id)

            if user:
                status_text = (
                    f'📊 Ваш статус:\n\n'
                    f'👤 Пользователь: {user.username}\n'
                    f'📱 Telegram ID: {chat_id}\n'
                    f'📧 Email: {user.email or "не указан"}\n\n'
                    f'📈 Статистика аренд:\n'
                    f'• Всего аренд: {total}\n'
                    f'• Активные: {active}\n'
                    f'• Ожидают подтверждения: {pending}\n\n'
                    f'✅ Аккаунт привязан'
                )
                await update.message.reply_text(status_text)
            else:
                await update.message.reply_text(
                    '❌ Ваш аккаунт не привязан.\n'
                    'Используйте /link <код> для привязки.'
                )

        except Exception as e:
            logger.error(f"Ошибка статуса: {e}")
            await update.message.reply_text("❌ Ошибка получения статуса.")

    @sync_to_async
    def _get_pending_rentals_sync(self, chat_id):
        """Синхронная функция для получения ожидающих аренд"""
        try:
            from rental.models import UserProfile, TelegramConfirmation
            from django.utils import timezone

            try:
                profile = UserProfile.objects.get(telegram_id=chat_id)
                user = profile.user

                pending_list = []

                confirmations = TelegramConfirmation.objects.filter(
                    user=user,
                    status='pending'
                ).select_related('rental', 'rental__car')

                for conf in confirmations:
                    if conf.rental.status == 'pending':
                        is_expired = conf.expires_at < timezone.now() if conf.expires_at else False

                        if not is_expired:
                            pending_list.append({
                                'rental': conf.rental,
                                'code': conf.confirmation_code,
                                'expires': conf.expires_at
                            })

                return user, pending_list
            except UserProfile.DoesNotExist:
                return None, []

        except Exception as e:
            logger.error(f"Ошибка в _get_pending_rentals_sync: {e}")
            return None, []

    async def pending(self, update, context):
        """Показать только аренды ожидающие подтверждения с кодами"""
        try:
            chat_id = update.effective_chat.id

            if not await self._check_django():
                await update.message.reply_text("❌ Системная ошибка.")
                return

            user, pending_list = await self._get_pending_rentals_sync(chat_id)

            if user is None:
                await update.message.reply_text("❌ Аккаунт не привязан.")
                return

            if not pending_list:
                await update.message.reply_text(
                    "📭 Нет аренд, ожидающих подтверждения.\n\n"
                    "Если у вас есть pending аренды без кодов, "
                    "свяжитесь с поддержкой для получения кода подтверждения."
                )
                return

            message = f'⏳ *Аренды для подтверждения/отмены ({len(pending_list)}):*\n\n'

            for item in pending_list:
                rental = item['rental']
                car_info = f"{rental.car.brand} {rental.car.model}" if rental.car else "Автомобиль"
                expires_str = item['expires'].strftime('%d.%m.%Y %H:%M') if item['expires'] else "не указан"

                message += (
                    f'🚗 *{car_info}*\n'
                    f'📅 {rental.start_date} - {rental.end_date}\n'
                    f'💰 {rental.total_price} BYN\n'
                    f'🆔 #{rental.id}\n'
                    f'🔐 *Код:* `{item["code"]}`\n'
                    f'⏰ *Действует до:* {expires_str}\n'
                    f'✅ *Подтвердить:* `/confirm {item["code"]}`\n'
                    f'❌ *Отменить:* `/cancel {item["code"]}`\n'
                    f'─' * 30 + '\n'
                )

            message += (
                '\n💡 *Быстрые команды:*\n'
                '• Скопируйте код и используйте команды выше\n'
                '• Или просто нажмите на команду чтобы отправить\n'
            )

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка в команде pending: {e}")
            await update.message.reply_text("❌ Ошибка получения списка.")

    def setup_handlers(self):
        """Настройка обработчиков"""
        from telegram.ext import CommandHandler, MessageHandler, filters

        # Команды
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("link", self.link_account))
        self.application.add_handler(CommandHandler("my_rentals", self.my_rentals))
        self.application.add_handler(CommandHandler("confirm", self.confirm_rental))
        self.application.add_handler(CommandHandler("cancel", self.cancel_rental))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("debug", self.debug_command))
        self.application.add_handler(CommandHandler("pending", self.pending))

        # Обработка обычных сообщений
        async def echo(update, context):
            await update.message.reply_text(
                "🤖 Я понимаю только команды.\n"
                "Используйте /help для списка команд."
            )

        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    def run(self):
        """Запуск бота"""
        if not self.token:
            logger.error("❌ TELEGRAM_BOT_TOKEN не установлен!")
            return

        try:
            from telegram.ext import Application
            from telegram import Update

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self.application = Application.builder().token(self.token).build()
            self.setup_handlers()

            logger.info("🤖 Бот запущен и ожидает сообщений...")
            print("=" * 60)
            print("💡 Откройте Telegram и напишите боту: /start")
            print("📝 Доступные команды: /link, /my_rentals, /confirm, /cancel, /status, /debug")
            print("⏳ Ожидание сообщений... (Ctrl+C для остановки)")
            print("=" * 60)

            loop.run_until_complete(
                self.application.run_polling(
                    drop_pending_updates=True,
                    timeout=20,
                    poll_interval=3,
                    allowed_updates=Update.ALL_TYPES
                )
            )

        except KeyboardInterrupt:
            logger.info("👋 Бот остановлен пользователем")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
        finally:
            if 'loop' in locals() and loop and not loop.is_closed():
                loop.close()


def get_token():
    """Получает токен из разных источников"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        try:
            init_django()
            from django.conf import settings
            token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        except:
            pass

    return token


def run_bot():
    """Основная функция запуска бота"""
    token = get_token()

    if not token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден!")
        print("💡 Используйте один из способов:")
        print("1. Экспорт: export TELEGRAM_BOT_TOKEN='ваш_токен'")
        print("2. При запуске: TELEGRAM_BOT_TOKEN='токен' python manage.py runbot")
        print("3. В settings.py: TELEGRAM_BOT_TOKEN = 'ваш_токен'")
        return

    print(f"✅ Токен получен: {token[:15]}...")
    print(f"✅ Django инициализирован: {DJANGO_INITIALIZED}")

    bot = TelegramBot(token)
    bot.run()


if __name__ == "__main__":
    run_bot()