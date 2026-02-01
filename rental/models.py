from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Car(models.Model):
    COLOR_CHOICES = [
        ('red', 'Красный'),
        ('blue', 'Синий'),
        ('black', 'Черный'),
        ('white', 'Белый'),
        ('silver', 'Серебристый'),
        ('gray', 'Серый'),
        ('green', 'Зеленый'),
        ('yellow', 'Желтый'),
    ]

    FUEL_CHOICES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('electric', 'Электрический'),
        ('hybrid', 'Гибрид'),
    ]

    TRANSMISSION_CHOICES = [
        ('manual', 'Механика'),
        ('automatic', 'Автомат'),
        ('robot', 'Робот'),
    ]

    brand = models.CharField(max_length=100, verbose_name='Марка')
    model = models.CharField(max_length=100, verbose_name='Модель')
    year = models.IntegerField(verbose_name='Год выпуска')

    color = models.CharField(
        max_length=20,
        choices=COLOR_CHOICES,
        verbose_name='Цвет'
    )

    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_CHOICES,
        verbose_name='Тип топлива'
    )

    transmission = models.CharField(
        max_length=20,
        choices=TRANSMISSION_CHOICES,
        verbose_name='Коробка передач'
    )

    seats = models.IntegerField(
        verbose_name='Количество мест',
        default=5
    )

    price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена за день (BYN)',
        validators=[MinValueValidator(0)]
    )

    is_available = models.BooleanField(default=True, verbose_name='Доступен')

    description = models.TextField(verbose_name='Описание')
    image = models.ImageField(
        upload_to='cars/',
        verbose_name='Изображение',
        blank=True,
        null=True
    )

    engine_volume = models.FloatField(verbose_name='Объем двигателя (л)')
    power = models.IntegerField(verbose_name='Мощность (л.с.)')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'

    def __str__(self):
        return f'{self.brand} {self.model} ({self.year})'

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum([review.rating for review in reviews]) / reviews.count(), 1)
        return 0

    @property
    def total_rentals(self):
        return self.rentals.filter(status='completed').count()


class Rental(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('active', 'Активна'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name='Пользователь'
    )

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='rentals',
        verbose_name='Автомобиль'
    )

    start_date = models.DateField(verbose_name='Дата начала')
    end_date = models.DateField(verbose_name='Дата окончания')
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Общая стоимость'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Аренда'
        verbose_name_plural = 'Аренды'

    def __str__(self):
        return f'Аренда #{self.id} - {self.car}'

    def save(self, *args, **kwargs):
        if not self.pk:
            days = (self.end_date - self.start_date).days + 1
            self.total_price = days * self.car.price_per_day
        super().save(*args, **kwargs)


class Review(models.Model):
    rental = models.OneToOneField(
        Rental,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Аренда'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автомобиль'
    )

    rating = models.IntegerField(
        verbose_name='Рейтинг',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ['rental', 'user']

    def __str__(self):
        return f'Отзыв на {self.car} от {self.user.username}'


class TelegramConfirmation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('rejected', 'Отклонена'),
        ('expired', 'Просрочена'),
    ]

    rental = models.OneToOneField(
        Rental,
        on_delete=models.CASCADE,
        related_name='telegram_confirmation',
        verbose_name='Аренда'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='telegram_confirmations',
        verbose_name='Пользователь'
    )

    chat_id = models.BigIntegerField(
        verbose_name='Telegram Chat ID',
        null=True,
        blank=True
    )

    confirmation_code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='Код подтверждения'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name='Действителен до')

    class Meta:
        verbose_name = 'Подтверждение Telegram'
        verbose_name_plural = 'Подтверждения Telegram'
        ordering = ['-created_at']

    def __str__(self):
        return f'Подтверждение #{self.id} для аренды #{self.rental.id}'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def generate_confirmation_code(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    telegram_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Telegram ID'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль {self.user.username}'