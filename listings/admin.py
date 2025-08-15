from django.contrib import admin
from .models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    # Columns shown in the listings changelist
    list_display = (
        "title",
        "landlord",
        "description",
        "location_city",
        "location_district",
        "price",
        "rooms",
        "housing_type",
        "status",
        "created_at",
        "views_count",
    )

    # Sidebar filters
    list_filter = (
        "housing_type",
        "status",
        "location_city",
    )

    # Search fields
    search_fields = (
        "title",
        "description",
        "location_city",
        "location_district",
    )

    # Inline-editable fields in the changelist
    list_editable = (
        "price",
        "status",
    )

    # Read-only fields in the form
    readonly_fields = (
        "created_at",
        "views_count",
    )
