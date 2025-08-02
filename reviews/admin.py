from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # Колонки в списке отзывов
    list_display = (
        'listing',
        'tenant',
        'rating',
        'short_comment',
        'created_at',
    )
    # Фильтры в правой панели
    list_filter = (
        'rating',
        'created_at',
        'listing__location_city',
    )
    # Поиск по полям и связям
    search_fields = (
        'tenant__username',
        'listing__title',
        'comment',
    )
    # Поля, доступные только для чтения
    readonly_fields = (
        'created_at',
    )

    def short_comment(self, obj):
        # укоротим длинный комментарий в списке
        short = obj.comment[:50] + ('…' if len(obj.comment) > 50 else '')
        return short

    short_comment.short_description = 'Comment'  # short_description задаёт, как именно эта колонка будет называться
                                                 # в таблице отзывов в Django Admin
