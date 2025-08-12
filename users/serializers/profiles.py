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
        qs = obj.get_current_bookings()
        return BookingSerializer(qs, many=True).data


class LandlordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    active_listings = serializers.SerializerMethodField(method_name='get_listings')

    class Meta:
        model = Landlord  # proxy of User
        fields = ('id', 'username', 'email', 'active_listings')

    def get_listings(self, obj):
        qs = obj.get_listings()
        return ListingSerializer(qs, many=True).data
