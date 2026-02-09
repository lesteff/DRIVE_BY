from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .forms import UserRegisterForm, RentalForm, ReviewForm, CarSearchForm


class FormTests(TestCase):
    """МИНИМАЛЬНЫЕ ТЕСТЫ ДЛЯ ФОРМ"""

    def test_user_register_form_works(self):
        """Тест формы регистрации - САМЫЙ ВАЖНЫЙ"""
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }

        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Ошибки: {form.errors}")
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')

    def test_rental_form_valid_dates(self):
        """Тест формы аренды с правильными датами"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        in_three_days = tomorrow + timedelta(days=2)

        form_data = {
            'start_date': tomorrow,
            'end_date': in_three_days,
        }

        form = RentalForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Ошибки: {form.errors}")

    def test_rental_form_invalid_dates(self):
        """Тест формы аренды с неправильными датами"""
        tomorrow = timezone.now().date() + timedelta(days=1)

        form_data = {
            'start_date': tomorrow,
            'end_date': tomorrow - timedelta(days=1),  # Вчера
        }

        form = RentalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors) > 0)

    def test_review_form_basic(self):
        """Тест формы отзыва"""
        form_data = {
            'rating': 5,
            'comment': 'Отличный автомобиль!',
        }

        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Ошибки: {form.errors}")

    def test_car_search_form_basic(self):
        """Тест формы поиска автомобилей"""
        form = CarSearchForm(data={})
        self.assertTrue(form.is_valid(), f"Ошибки: {form.errors}")
        form_data = {
            'brand': 'Toyota',
            'color': 'black',
            'min_price': 20,
            'max_price': 100,
        }

        form = CarSearchForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Ошибки: {form.errors}")


class ViewTests(TestCase):
    """МИНИМАЛЬНЫЕ ТЕСТЫ ДЛЯ ПРЕДСТАВЛЕНИЙ"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_home_page_works(self):
        """Тест что главная страница открывается"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html')

    def test_register_page_works(self):
        """Тест что страница регистрации открывается"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form')

    def test_car_list_page_works(self):
        """Тест что страница списка автомобилей открывается"""
        response = self.client.get(reverse('car_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html')

    def test_register_form_creates_user(self):
        """Тест что форма регистрации создает пользователя"""
        form_data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'first_name': 'Тест',
            'last_name': 'Пользователь',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertTrue(User.objects.filter(username='testuser2').exists())
        self.assertEqual(response.status_code, 302)

    def test_protected_pages_require_login(self):
        """Тест что защищенные страницы требуют входа"""
        protected_urls = [
            reverse('my_rentals'),
            reverse('link_telegram'),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue('next=' in response.url or 'login' in response.url)


