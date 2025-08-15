from django.utils import timezone
from rest_framework import serializers

from .models import Review
from bookings.models import Booking
from bookings.choices import BookingStatus
from django.contrib.auth import get_user_model

User = get_user_model()


class UserShortSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class ReviewSerializer(serializers.ModelSerializer):
    # The author of the review is taken from request.user
    tenant = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tenant_info = UserShortSerializers(source='tenant', read_only=True)

    # The client sends only the booking; we'll set listing automatically
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    listing = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'booking', 'listing', 'tenant_info', 'tenant', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'tenant', 'listing', 'created_at')
        extra_kwargs = {
            # Optional to hide in responses, but still required on create
            'booking': {'write_only': True}
        }

    def validate(self, attrs):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Authentication is required.")

        booking = attrs.get('booking') or getattr(self.instance, 'booking', None)
        if booking is None:
            raise serializers.ValidationError({"booking": "This field is required."})

        # Landlord cannot review their own listing
        if booking.listing.landlord_id == user.id:
            raise serializers.ValidationError("You cannot leave a review for your own listing.")

        # The booking must belong to the current user
        if booking.tenant_id != user.id:
            raise serializers.ValidationError("You can only review your own booking.")

        # Booking must be confirmed and already finished
        today = timezone.localdate()
        if booking.status != BookingStatus.CONFIRMED:
            raise serializers.ValidationError("Reviews are allowed only for confirmed bookings.")
        if booking.end_date > today:
            raise serializers.ValidationError("You can leave a review only after the stay has ended.")

        # Only one review per booking per tenant
        qs = Review.objects.filter(tenant_id=user.id, booking_id=booking.id)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A review for this booking has already been submitted.")

        # Lock listing to the one from booking and prevent spoofing
        attrs['listing'] = booking.listing

        # On update, booking cannot be changed
        if self.instance and booking.id != self.instance.booking_id:
            raise serializers.ValidationError("You cannot change the booking on an existing review.")

        return attrs
