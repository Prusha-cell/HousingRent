from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    # Columns in the reviews list
    list_display = (
        'listing',
        'tenant',
        'rating',
        'short_comment',
        'created_at',
    )
    # Filters in the right sidebar
    list_filter = (
        'rating',
        'created_at',
        'listing__location_city',
    )
    # Search by fields and related fields
    search_fields = (
        'tenant__username',
        'listing__title',
        'comment',
    )
    # Read-only fields in the form
    readonly_fields = (
        'created_at',
    )

    def short_comment(self, obj):
        """Trim long comments in the changelist table."""
        text = obj.comment or ""
        return text[:50] + ('…' if len(text) > 50 else '')

    short_comment.short_description = 'Comment'
