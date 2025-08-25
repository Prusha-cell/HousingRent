from django.utils import timezone

from bookings.choices import BookingStatus
from listings.choices import ListingStatus
from users.models import Tenant, Landlord
from bookings.serializers import BookingSerializer
from listings.serializers import ListingSerializer
from rest_framework import serializers


class TenantSerializer(serializers.ModelSerializer):

    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    current_bookings = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = ('id', 'username', 'email', 'current_bookings')

    def get_current_bookings(self, obj):
        data = getattr(obj, "prefetched_current_bookings", None)
        if data is None:
            qs = (
                obj.bookings
                .filter(status=BookingStatus.CONFIRMED,
                        end_date__gte=timezone.localdate())
                .only("id", "listing_id", "tenant_id", "start_date", "end_date", "status", "created_at")
            )
            data = list(qs)
        return BookingSerializer(data, many=True).data


class LandlordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    active_listings = serializers.SerializerMethodField()

    class Meta:
        model = Landlord  # proxy of User
        fields = ('id', 'username', 'email', 'active_listings')

    def get_active_listings(self, obj):
        data = getattr(obj, "prefetched_active_listings", None)
        if data is None:
            qs = (
                obj.listings
                .filter(status=ListingStatus.AVAILABLE)
                .only("id", "title", "description", "location_city", "location_district",
                      "price", "rooms", "housing_type", "status", "created_at", "views_count", "landlord_id")
            )
            data = list(qs)
        return ListingSerializer(data, many=True).data
