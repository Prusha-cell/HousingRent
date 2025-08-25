from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Listing
from .serializers import ListingSerializer
from .choices import ListingStatus
from analytics.models import SearchHistory, ListingView
from utils.permissions import IsLandlordOrReadOnly, IsLandlordOwnerOnly


class ListingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public listings (read-only):
    - Anyone can use GET/HEAD/OPTIONS.
    - Search over title/description/location_*.
    - Field filtering + ordering.
    - Logs search queries to SearchHistory.
    """
    queryset = Listing.objects.select_related("landlord").all()
    serializer_class = ListingSerializer
    permission_classes = [IsLandlordOrReadOnly]

    # Filters/search/ordering — visible in DRF Browsable API
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "status": ["exact"],
        "location_city": ["exact"],
        "location_district": ["exact"],
        "rooms": ["gte", "lte"],
        "housing_type": ["exact"],
        "price": ["gte", "lte"],
    }
    search_fields = ["title", "description", "location_city", "location_district"]
    ordering_fields = ["created_at", "price", "views_count"]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Log a single view per user per day
        if request.user.is_authenticated:
            today = timezone.localdate()
            with transaction.atomic():
                _, _created = ListingView.objects.get_or_create(
                    user=request.user,
                    listing=instance,
                    viewed_on=today,
                )

        return super().retrieve(request, *args, **kwargs)

    # If you want the public endpoint to show ONLY available listings:
    def get_queryset(self):
        return super().get_queryset().filter(status=ListingStatus.AVAILABLE)

    def list(self, request, *args, **kwargs):
        """
        Log searches if ?search=... or ?q=... is provided
        (DRF's SearchFilter uses the `search` parameter).
        """
        keyword = (request.query_params.get("search") or request.query_params.get("q") or "").strip()
        if keyword:
            SearchHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                keyword=keyword,
            )
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Alternative endpoint: /api/listings/search/?q=...
        Works together with standard filters (?status=..., ?ordering=..., ?search=...).
        Will appear as a "GET" button in Extra actions in the browsable API.
        """
        q = (request.query_params.get("q") or "").strip()

        # Apply ALL standard filters/search/ordering so ?status=..., ?ordering=..., ?search=... keep working
        qs = self.filter_queryset(self.get_queryset())

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
            SearchHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                keyword=q,
            )

        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data)


class MyListingViewSet(viewsets.ModelViewSet):
    serializer_class = ListingSerializer
    permission_classes = [IsLandlordOwnerOnly]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Listing.objects.all()
        # Critical: only expose the current user's own listings
        return Listing.objects.filter(landlord_id=user.pk)
