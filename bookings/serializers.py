from django.utils import timezone
from rest_framework import serializers

from listings.choices import ListingStatus
from .models import Booking
from .choices import BookingStatus


class BookingSerializer(serializers.ModelSerializer):
    """
    Booking serializer with business validations:
    - Listing must be AVAILABLE.
    - start_date < end_date.
    - start_date must not be in the past.
    - No overlap with existing PENDING/CONFIRMED bookings for the same listing.
    """
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Booking
        fields = ("id", "listing", "tenant", "start_date", "end_date", "status", "created_at")
        read_only_fields = ("id", "tenant", "status")

    def validate(self, attrs):
        inst = getattr(self, "instance", None)
        listing = attrs.get("listing") or (inst.listing if inst else None)
        start = attrs.get("start_date") or (inst.start_date if inst else None)
        end = attrs.get("end_date") or (inst.end_date if inst else None)

        # If any of these are missing, let field-level validation handle it.
        if not listing or not start or not end:
            return attrs

        if listing.status != ListingStatus.AVAILABLE:
            raise serializers.ValidationError(
                "This listing is currently not available for booking."
            )

        if start >= end:
            raise serializers.ValidationError("start_date must be earlier than end_date.")

        today = timezone.localdate()
        if start < today:
            raise serializers.ValidationError("Cannot book past dates (start_date is in the past).")

        busy_statuses = (BookingStatus.CONFIRMED, BookingStatus.PENDING)
        qs = Booking.objects.filter(
            listing=listing,
            status__in=busy_statuses,
            start_date__lt=end,  # overlap if (a.start < b.end) AND
            end_date__gt=start,  #            (a.end > b.start)
        )
        if inst:
            qs = qs.exclude(pk=inst.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "This period overlaps with an existing booking or reservation for the listing."
            )

        return attrs
