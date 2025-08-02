from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # Поля, которые будут отображаться в списке бронирования
    list_display = (
        'listing',
        'tenant',
        'start_date',
        'end_date',
        'status',
        'created_at',
    )
    # По каким полям можно фильтровать в боковой панели
    list_filter = (
        'status',
        'listing__location_city',
        'tenant__username',
    )
    # По каким полям будет работать поиск
    search_fields = (
        'listing__title',
        'tenant__username',
        'start_date',
        'end_date',
    )
    # Поля, доступные для редактирования прямо в списке
    list_editable = (
        'start_date',
        'end_date',
        'status',
    )
    # Какие поля показывать только для чтения
    readonly_fields = (
        'created_at',
    )
