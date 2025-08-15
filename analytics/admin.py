from django.contrib import admin
from .models import SearchHistory, ListingView


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for SearchHistory."""
    # Columns in the changelist
    list_display = ("user", "keyword", "searched_at")
    # Right-side filters
    list_filter = ("keyword", "user")
    # Search by keyword and username
    search_fields = ("keyword", "user__username")
    # Date navigation
    date_hierarchy = "searched_at"
    # Read-only fields
    readonly_fields = ("searched_at",)


@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    """Admin configuration for ListingView."""
    list_display = ("user", "listing", "viewed_at")
    list_filter = ("listing", "user")
    search_fields = ("listing__title", "user__username")
    date_hierarchy = "viewed_at"
    readonly_fields = ("viewed_at",)
