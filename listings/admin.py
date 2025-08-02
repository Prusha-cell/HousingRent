from django.contrib import admin
from .models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке объявлений
    list_display = (
        'title',
        'landlord',
        'description',
        'location_city',
        'location_district',
        'price',
        'rooms',
        'housing_type',
        'status',
        'created_at',
        'views_count',
    )
    # По каким полям можно фильтровать в боковой панели
    list_filter = (
        'housing_type',
        'status',
        'location_city',
    )
    # По каким полям будет работать поиск
    search_fields = (
        'title',
        'description',
        'location_city',
        'location_district',
    )
    # Поля, доступные для редактирования прямо в списке
    list_editable = (
        'price',
        'status',
    )
    # Какие поля показывать только для чтения
    readonly_fields = (
        'created_at',
        'views_count',
    )
