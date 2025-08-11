from django.utils import timezone
from rest_framework import serializers

from listings.choices import ListingStatus
from .models import Booking
from .choices import BookingStatus


class BookingSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Booking
        fields = ('id', 'listing', 'tenant', 'start_date', 'end_date', 'status', 'created_at')
        read_only_fields = ('id', 'tenant', 'status')

    def validate(self, attrs):
        inst = self.instance
        listing = attrs.get('listing') or (inst and inst.listing)
        start = attrs.get('start_date') or (inst and inst.start_date)
        end = attrs.get('end_date') or (inst and inst.end_date)

        if listing.status != ListingStatus.AVAILABLE:
            raise serializers.ValidationError(
                "Это объявление сейчас недоступно для бронирования."
            )

        if not listing or not start or not end:
            return attrs

        if start >= end:
            raise serializers.ValidationError("start_date должен быть раньше end_date.")

        today = timezone.now().date()  # или timezone.localdate()
        if start < today:
            raise serializers.ValidationError("Нельзя бронировать на прошедшие даты (start_date в прошлом).")

        busy_statuses = [BookingStatus.CONFIRMED, BookingStatus.PENDING]

        qs = Booking.objects.filter(
            listing=listing,
            status__in=busy_statuses,
            start_date__lt=end,  # (a.start < b.end) AND
            end_date__gt=start,  # (a.end > b.start) → пересечение
        )
        if inst:
            qs = qs.exclude(pk=inst.pk)

        if qs.exists():
            raise serializers.ValidationError("На эти даты уже есть бронь или резерв для этого объявления.")

        return attrs
