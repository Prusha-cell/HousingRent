from rest_framework import serializers
from .models import Listing


class ListingSerializer(serializers.ModelSerializer):
    # скрытое поле, текущее user станет landlord
    landlord = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

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
            'landlord',
        )
        read_only_fields = ('created_at', 'views_count')
