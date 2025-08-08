from rest_framework import viewsets

from utils.permissions import IsLandlordOrReadOnly, IsLandlordOwnerOnly
from .models import Listing
from .serializers import ListingSerializer


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [IsLandlordOrReadOnly]


class MyListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsLandlordOwnerOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Listing.objects.all()
        # критично: оставляем в queryset только свои объявления
        return Listing.objects.filter(landlord_id=user.pk)
