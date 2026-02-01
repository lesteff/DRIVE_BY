from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Car, Rental, Review
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
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().date()
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=(timezone.now() + timedelta(days=3)).date()
    )

    class Meta:
        model = Rental
        fields = ['start_date', 'end_date']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date < timezone.now().date():
                raise forms.ValidationError("Дата начала не может быть в прошлом")

            if end_date <= start_date:
                raise forms.ValidationError("Дата окончания должна быть позже даты начала")

            if (end_date - start_date).days > 30:
                raise forms.ValidationError("Максимальный срок аренды - 30 дней")

        return cleaned_data


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