import logging
from django.utils import timezone
from rental.models import TelegramConfirmation, Rental

logger = logging.getLogger(__name__)

def confirm_rental_sync(confirmation_code, chat_id):
    """Синхронная функция для подтверждения аренды"""
    try:
        logger.info(f"Поиск кода подтверждения: {confirmation_code}")

        # Ищем подтверждение
        confirmation = TelegramConfirmation.objects.select_related(
            'rental', 'rental__car', 'user'
        ).get(
            confirmation_code=confirmation_code,
            status='pending'
        )

        logger.info(f"Найдено подтверждение: {confirmation.id}")

        # Проверяем срок действия
        if confirmation.is_expired():
            confirmation.status = 'expired'
            confirmation.save()
            logger.warning(f"Код {confirmation_code} просрочен")
            return None, "Код подтверждения просрочен."

        # Проверяем chat_id
        if confirmation.chat_id and str(confirmation.chat_id) != str(chat_id):
            logger.warning(f"Chat ID mismatch: {confirmation.chat_id} != {chat_id}")
            return None, "Этот код подтверждения предназначен другому пользователю."

        # Устанавливаем chat_id если его нет
        if not confirmation.chat_id:
            confirmation.chat_id = chat_id
            logger.info(f"Установлен chat_id: {chat_id}")

        # Обновляем статус
        confirmation.status = 'confirmed'
        confirmation.confirmed_at = timezone.now()
        confirmation.save()

        # Обновляем статус аренды
        rental = confirmation.rental
        rental.status = 'active'
        rental.save()

        logger.info(f"Аренда {rental.id} подтверждена успешно")
        return rental, None

    except TelegramConfirmation.DoesNotExist:
        logger.error(f"Код подтверждения не найден: {confirmation_code}")
        return None, "Код подтверждения не найден."
    except Exception as e:
        logger.error(f"Ошибка при подтверждении аренды: {str(e)}", exc_info=True)
        return None, f"Внутренняя ошибка: {str(e)}"


def get_pending_codes():
    """Получение всех активных кодов (для отладки)"""
    codes = TelegramConfirmation.objects.filter(
        status='pending'
    ).values_list('confirmation_code', flat=True)
    return list(codes)


def get_code_details(confirmation_code):
    """Получение деталей кода (для отладки)"""
    try:
        confirmation = TelegramConfirmation.objects.select_related(
            'rental', 'rental__car', 'user'
        ).get(confirmation_code=confirmation_code)

        return {
            'code': confirmation.confirmation_code,
            'status': confirmation.status,
            'chat_id': confirmation.chat_id,
            'expires_at': confirmation.expires_at,
            'user': confirmation.user.username if confirmation.user else None,
            'car': f"{confirmation.rental.car.brand} {confirmation.rental.car.model}" if confirmation.rental and confirmation.rental.car else None,
            'rental_id': confirmation.rental.id if confirmation.rental else None,
        }
    except TelegramConfirmation.DoesNotExist:
        return None