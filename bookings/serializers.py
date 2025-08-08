from rest_framework import serializers
from .models import Booking
from .choices import BookingStatus


class BookingSerializer(serializers.ModelSerializer):
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Booking
        fields = ('id', 'listing', 'start_date', 'end_date', 'status', 'tenant')
        read_only_fields = ('id', 'tenant')

    def validate(self, attrs):
        inst = self.instance
        listing = attrs.get('listing') or (inst and inst.listing)
        start = attrs.get('start_date') or (inst and inst.start_date)
        end = attrs.get('end_date') or (inst and inst.end_date)

        if not listing or not start or not end:
            return attrs

        if start >= end:
            raise serializers.ValidationError("start_date должен быть раньше end_date.")

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
            raise serializers.ValidationError("На эти даты уже есть бронь для этого объявления.")

        return attrs
