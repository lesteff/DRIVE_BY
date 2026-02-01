from django.contrib import admin
from .models import Car, Rental, Review

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'color', 'price_per_day', 'is_available')
    list_filter = ('brand', 'color', 'fuel_type', 'transmission', 'is_available')
    search_fields = ('brand', 'model', 'description')
    list_editable = ('price_per_day', 'is_available')

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'car', 'start_date', 'end_date', 'total_price', 'status')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('user__username', 'car__brand', 'car__model')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'car__brand', 'car__model', 'comment')