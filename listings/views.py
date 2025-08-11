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
    Публичная выдача объявлений (только чтение):
    - всем доступны GET/HEAD/OPTIONS;
    - поиск по title/description/location_*;
    - фильтры по полям + сортировка;
    - логирование поисковых запросов в SearchHistory.
    """
    queryset = Listing.objects.select_related('landlord').all()
    serializer_class = ListingSerializer
    permission_classes = [IsLandlordOrReadOnly]

    # Фильтры/поиск/сортировка — видны в DRF Browsable API
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'status': ['exact'],
        'location_city': ['exact'],
        'location_district': ['exact'],
        'rooms': ['gte', 'lte'],
        'housing_type': ['exact'],
        'price': ['gte', 'lte'],
    }
    search_fields = ['title', 'description', 'location_city', 'location_district']
    ordering_fields = ['created_at', 'price', 'views_count']

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # логируем просмотр один раз в сутки для каждого пользователя
        if request.user.is_authenticated:
            today = timezone.localdate()
            already = ListingView.objects.filter(
                user=request.user, listing=instance, viewed_at__date=today
            ).exists()
            if not already:
                ListingView.objects.create(user=request.user, listing=instance)
                # инкрементим счётчик просмотров
                Listing.objects.filter(pk=instance.pk).update(
                    views_count=F('views_count') + 1
                )

        return super().retrieve(request, *args, **kwargs)

    # Если хочешь показывать всем (включая анонимов) ТОЛЬКО доступные:
    def get_queryset(self):
        return super().get_queryset().filter(status=ListingStatus.AVAILABLE)

    def list(self, request, *args, **kwargs):
        """
        Логируем поиск, если пришли ?search=... или ?q=...
        (SearchFilter использует параметр `search`).
        """
        keyword = (request.query_params.get('search')
                   or request.query_params.get('q') or '').strip()
        if keyword:
            SearchHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                keyword=keyword
            )
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Альтернативный эндпоинт: /api/listings/search/?q=...
        Работает вместе со стандартными фильтрами (?status=..., ?ordering=... и т.д.).
        Появится кнопкой "GET" в Extra actions в браузабле.
        """
        q = (request.query_params.get('q') or '').strip()

        # применяем ВСЕ стандартные фильтры/поиск/сортировку,
        # чтобы работали ?status=..., ?ordering=..., ?search=...
        qs = self.filter_queryset(self.get_queryset())

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
            SearchHistory.objects.create(
                user=request.user if request.user.is_authenticated else None,
                keyword=q
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
        # критично: оставляем в queryset только свои объявления
        return Listing.objects.filter(landlord_id=user.pk)
