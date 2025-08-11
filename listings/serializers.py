from rest_framework import serializers

from .choices import ListingStatus
from .models import Listing


class ListingSerializer(serializers.ModelSerializer):
    # скрытое поле, текущее user станет landlord
    landlord = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    is_bookable = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        # убрали 'landlord' из обычных полей, потому что он HiddenField
        fields = (
            'id',
            'title',
            'description',
            'location_city',
            'location_district',
            'price',
            'rooms',
            'housing_type',
            'status',
            'is_bookable',
            'landlord',
            'created_at',
            'views_count',
        )
        read_only_fields = ('created_at', 'views_count')

    def get_is_bookable(self, obj):
        return obj.status == ListingStatus.AVAILABLE
