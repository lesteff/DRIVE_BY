from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Car, Rental, Review, UserProfile
from .forms import RentalForm, ReviewForm, CarSearchForm, UserRegisterForm, ProfileForm, UserForm
from django.utils import timezone
from datetime import timedelta
import random
import string
from .models import TelegramConfirmation
import logging
from .auth_views import user_login, user_logout

logger = logging.getLogger(__name__)



def home(request):
    cars = Car.objects.filter(is_available=True)[:6]
    form = CarSearchForm()
    return render(request, 'rental/home.html', {'cars': cars, 'form': form})


def car_list(request):
    cars = Car.objects.filter(is_available=True)
    form = CarSearchForm(request.GET)

    if form.is_valid():
        brand = form.cleaned_data.get('brand')
        color = form.cleaned_data.get('color')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        fuel_type = form.cleaned_data.get('fuel_type')
        transmission = form.cleaned_data.get('transmission')

        if brand:
            cars = cars.filter(brand__icontains=brand)
        if color:
            cars = cars.filter(color=color)
        if min_price:
            cars = cars.filter(price_per_day__gte=min_price)
        if max_price:
            cars = cars.filter(price_per_day__lte=max_price)
        if fuel_type:
            cars = cars.filter(fuel_type=fuel_type)
        if transmission:
            cars = cars.filter(transmission=transmission)

    paginator = Paginator(cars, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'rental/car_list.html', {
        'page_obj': page_obj,
        'form': form
    })


def car_detail(request, car_id):
    car = get_object_or_404(Car, id=car_id)
    reviews = car.reviews.all().order_by('-created_at')

    # Получаем занятые даты для отображения в календаре
    unavailable_dates = car.get_unavailable_dates()

    can_review = False
    if request.user.is_authenticated:
        completed_rentals = Rental.objects.filter(
            user=request.user,
            car=car,
            status='completed'
        )
        has_review = Review.objects.filter(
            user=request.user,
            car=car
        ).exists()
        can_review = completed_rentals.exists() and not has_review

    return render(request, 'rental/car_detail.html', {
        'car': car,
        'reviews': reviews,
        'can_review': can_review,
        'unavailable_dates': unavailable_dates
    })


@login_required
def rent_car(request, car_id):
    car = get_object_or_404(Car, id=car_id)

    if request.method == 'POST':
        form = RentalForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            # Используем метод модели для проверки
            is_available, message = car.is_available_for_dates(start_date, end_date)

            if not is_available:
                messages.error(request, message)
                return render(request, 'rental/rent_car.html', {
                    'car': car,
                    'form': form
                })

            # Дополнительные проверки...
            max_rental_days = 30
            rental_days = (end_date - start_date).days + 1
            if rental_days > max_rental_days:
                messages.error(
                    request,
                    f'Максимальный срок аренды - {max_rental_days} дней'
                )
                return render(request, 'rental/rent_car.html', {
                    'car': car,
                    'form': form
                })

            # Создаем аренду
            rental = form.save(commit=False)
            rental.user = request.user
            rental.car = car
            rental.status = 'pending'  # Ожидает подтверждения

            # Расчет общей стоимости
            price_per_day = car.price_per_day
            total_price = price_per_day * rental_days
            rental.total_price = total_price

            rental.save()

            # Создаем код подтверждения
            confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

            telegram_confirmation = TelegramConfirmation.objects.create(
                rental=rental,
                user=request.user,
                confirmation_code=confirmation_code,
                expires_at=timezone.now() + timedelta(hours=24),
                # Добавляем chat_id если он известен
                chat_id=request.user.profile.telegram_id if hasattr(request.user,
                                                                    'profile') and request.user.profile.telegram_id else None
            )

            # Отправляем уведомление в Telegram если привязан
            if hasattr(request.user, 'profile') and request.user.profile.telegram_id:
                chat_id = request.user.profile.telegram_id
                message = (
                    f"🚗 *Новая аренда требует подтверждения!*\n\n"
                    f"Автомобиль: {car.brand} {car.model}\n"
                    f"Даты: {rental.start_date} - {rental.end_date}\n"
                    f"Стоимость: {rental.total_price} BYN\n\n"
                    f"🔑 *Код подтверждения:* `{confirmation_code}`\n\n"
                    f"✅ Подтвердить: /confirm {confirmation_code}\n"
                    f"❌ Отменить: /cancel {confirmation_code}\n\n"
                    f"Код действителен 24 часа."
                )


                messages.success(
                    request,
                    'Заявка на аренду создана! Проверьте Telegram для подтверждения.'
                )
            else:
                messages.success(
                    request,
                    f'Заявка на аренду создана! Код подтверждения: {confirmation_code}\n'
                    f'Привяжите Telegram для удобного подтверждения.'
                )

            return redirect('my_rentals')
    else:
        form = RentalForm()

    return render(request, 'rental/rent_car.html', {
        'car': car,
        'form': form
    })


@login_required
def cancel_rental(request, rental_id):
    """
    Представление для отмены аренды
    """
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)

    if rental.status not in ['pending', 'active']:
        messages.error(
            request,
            f'Невозможно отменить аренду со статусом "{rental.get_status_display()}"'
        )
        return redirect('my_rentals')

    if rental.start_date <= timezone.now().date():
        messages.error(
            request,
            'Невозможно отменить аренду после даты её начала'
        )
        return redirect('my_rentals')

    if request.method == 'POST':
        try:
            old_status = rental.status
            rental.status = 'cancelled'
            rental.cancellation_reason = request.POST.get('reason', '')
            rental.cancelled_at = timezone.now()
            rental.save()

            if rental.car:
                rental.car.is_available = True
                rental.car.save()

            if hasattr(rental, 'telegram_confirmation'):
                telegram_conf = rental.telegram_confirmation
                if telegram_conf.status == 'pending':
                    telegram_conf.status = 'cancelled'
                    telegram_conf.save()

            messages.success(request, 'Аренда успешно отменена')

            logger.info(
                f'Rental {rental_id} cancelled by user {request.user.id}. '
                f'Old status: {old_status}, New status: cancelled'
            )

        except Exception as e:
            logger.error(f'Error cancelling rental {rental_id}: {str(e)}')
            messages.error(request, 'Произошла ошибка при отмене аренды')

        return redirect('my_rentals')

    return render(request, 'rental/cancel_rental.html', {
        'rental': rental
    })

@login_required
def my_rentals(request):
    rentals = Rental.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'rental/my_rentals.html', {'rentals': rentals})


@login_required
def add_review(request, rental_id):
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)

    if rental.status != 'completed':
        messages.error(request, 'Можно оставлять отзывы только на завершенные аренды')
        return redirect('my_rentals')

    if hasattr(rental, 'review'):
        messages.error(request, 'Вы уже оставили отзыв на эту аренду')
        return redirect('my_rentals')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.rental = rental
            review.user = request.user
            review.car = rental.car
            review.save()

            messages.success(request, 'Спасибо за ваш отзыв!')
            return redirect('car_detail', car_id=rental.car.id)
    else:
        form = ReviewForm()

    return render(request, 'rental/add_review.html', {
        'form': form,
        'rental': rental
    })


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'rental/register.html', {'form': form})


def logout_view(request):
    """Простой выход"""
    logout(request)
    from django.contrib import messages
    messages.success(request, 'Вы успешно вышли из системы')
    from django.shortcuts import redirect
    return redirect('home')


@login_required
def profile_view(request):
    """Просмотр и редактирование профиля"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    # Получаем статистику
    rentals_count = Rental.objects.filter(user=request.user).count()
    active_rentals = Rental.objects.filter(
        user=request.user,
        status__in=['pending', 'active']
    ).count()
    reviews_count = Review.objects.filter(user=request.user).count()

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    return render(request, 'rental/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'rentals_count': rentals_count,
        'active_rentals': active_rentals,
        'reviews_count': reviews_count
    })

@login_required
def link_telegram(request):
    """Страница привязки Telegram"""
    return render(request, 'rental/link_telegram.html')