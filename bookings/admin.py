from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """Admin configuration for Booking."""
    # Columns shown in the changelist
    list_display = (
        "listing",
        "tenant",
        "start_date",
        "end_date",
        "status",
        "created_at",
    )
    # Sidebar filters
    list_filter = (
        "status",
        "listing__location_city",
        "tenant__username",
    )
    # Search fields
    search_fields = (
        "listing__title",
        "tenant__username",
        "start_date",
        "end_date",
    )
    # Inline editable fields in the list view
    list_editable = (
        "start_date",
        "end_date",
        "status",
    )
    # Read-only fields in the form
    readonly_fields = (
        "created_at",
    )
