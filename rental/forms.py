from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Car, Rental, Review, UserProfile
from django.utils import timezone
from datetime import timedelta


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


class RentalForm(forms.ModelForm):
    class Meta:
        model = Rental
        fields = ['start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            # Проверка что даты корректны
            if start_date < timezone.now().date():
                raise ValidationError({
                    'start_date': 'Дата начала аренды не может быть в прошлом'
                })

            if end_date < start_date:
                raise ValidationError({
                    'end_date': 'Дата окончания не может быть раньше даты начала'
                })

            # Проверка на максимальный срок
            max_days = 30
            rental_days = (end_date - start_date).days + 1
            if rental_days > max_days:
                raise ValidationError(
                    f'Максимальный срок аренды - {max_days} дней'
                )

            # Проверка на минимальный срок
            min_days = 1
            if rental_days < min_days:
                raise ValidationError(
                    f'Минимальный срок аренды - {min_days} день'
                )

        return cleaned_data

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')

        # Нельзя бронировать на сегодня если уже поздно (опционально)
        if start_date == timezone.now().date() and timezone.now().hour >= 18:
            raise ValidationError(
                'Бронирование на сегодня возможно только до 18:00'
            )

        return start_date

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }


class CarSearchForm(forms.Form):
    brand = forms.CharField(required=False, max_length=100, label='Марка')
    color = forms.ChoiceField(
        required=False,
        choices=[('', 'Любой')] + Car.COLOR_CHOICES,
        label='Цвет'
    )
    min_price = forms.IntegerField(
        required=False,
        min_value=0,
        label='Минимальная цена'
    )
    max_price = forms.IntegerField(
        required=False,
        min_value=0,
        label='Максимальная цена'
    )
    fuel_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Любой')] + Car.FUEL_CHOICES,
        label='Тип топлива'
    )
    transmission = forms.ChoiceField(
        required=False,
        choices=[('', 'Любая')] + Car.TRANSMISSION_CHOICES,
        label='Коробка передач'
    )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone']