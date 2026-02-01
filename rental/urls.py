from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('cars/', views.car_list, name='car_list'),
    path('cars/<int:car_id>/', views.car_detail, name='car_detail'),
    path('cars/<int:car_id>/rent/', views.rent_car, name='rent_car'),
    path('my-rentals/', views.my_rentals, name='my_rentals'),
    path('cancel-rental/<int:rental_id>/', views.cancel_rental, name='cancel_rental'),
    path('rental/<int:rental_id>/review/', views.add_review, name='add_review'),
    path('link-telegram/', views.link_telegram, name='link_telegram'),

    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='rental/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]