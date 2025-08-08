# bookings/views.py
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError

from .models import Booking
from .serializers import BookingSerializer
from utils.permissions import IsBookingActorOrAdmin
from listings.models import Listing


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsBookingActorOrAdmin]

    def get_queryset(self):
        u = self.request.user
        qs = Booking.objects.select_related("listing")
        if u.is_staff or u.is_superuser:
            return qs
        # обычный пользователь/арендодатель видит свои брони
        # И брони по своим объявлениям
        return qs.filter(
            Q(tenant_id=u.pk) | Q(listing__landlord_id=u.pk)
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        listing = serializer.validated_data["listing"]

        # нельзя бронировать своё же объявление
        if listing.landlord_id == user.pk:
            raise ValidationError("Нельзя бронировать собственное объявление.")

        # защищаемся от гонок: транзакция + блокировка строки объявления
        # (на SQLite select_for_update — no-op; на MySQL/Postgres работает как надо)
        with transaction.atomic():
            Listing.objects.select_for_update().get(pk=listing.pk)
            serializer.save(tenant=user)

    def perform_update(self, serializer):
        with transaction.atomic():
            listing = serializer.validated_data.get("listing") or serializer.instance.listing
            Listing.objects.select_for_update().get(pk=listing.pk)
            serializer.save()
