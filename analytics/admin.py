from django.contrib import admin
from .models import SearchHistory, ListingView


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    # Столбцы в списке
    list_display = ('user', 'keyword', 'searched_at')
    # Фильтры справа
    list_filter = ('keyword', 'user')
    # Поиск по ключевым словам и по имени пользователя
    search_fields = ('keyword', 'user__username')
    # Навигация по дате
    date_hierarchy = 'searched_at'
    # Поле только для чтения
    readonly_fields = ('searched_at',)


@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'listing', 'viewed_at')
    list_filter = ('listing', 'user')
    search_fields = ('listing__title', 'user__username')
    date_hierarchy = 'viewed_at'
    readonly_fields = ('viewed_at',)
