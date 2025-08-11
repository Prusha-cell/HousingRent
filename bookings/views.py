from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.exceptions import ValidationError

from .models import Booking
from .serializers import BookingSerializer
from utils.permissions import IsBookingActorOrAdmin
from listings.models import Listing

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as drf_status
from .choices import BookingStatus

from django.conf import settings
from django.utils import timezone
import datetime


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

        # --- helpers -------------------------------------------------------------

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def _is_landlord_of(self, user, booking):
        return getattr(booking.listing, "landlord_id", None) == user.pk

    def _is_tenant_of(self, user, booking):
        return getattr(booking, "tenant_id", None) == user.pk

        # --- actions -------------------------------------------------------------

    @action(detail=True, methods=['get', 'post'])
    def confirm(self, request, pk=None):
        """
        Подтвердить бронь — доступно лендлорду объявления и админам.
        GET: подсказка. POST: меняет статус на CONFIRMED.
        """
        booking = self.get_object()
        user = request.user

        if request.method == 'GET':
            return Response({
                "detail": "Используйте POST для подтверждения брони.",
                "current_status": booking.status
            })

        if not (self._is_admin(user) or self._is_landlord_of(user, booking)):
            return Response({"detail": "Недостаточно прав."}, status=drf_status.HTTP_403_FORBIDDEN)

        if booking.status in (BookingStatus.CANCELLED, BookingStatus.REJECTED):
            return Response({"detail": f"Нельзя подтвердить бронь в статусе {booking.status}."},
                            status=drf_status.HTTP_400_BAD_REQUEST)
        if booking.status == BookingStatus.CONFIRMED:
            return Response({"detail": "Бронь уже подтверждена."}, status=drf_status.HTTP_400_BAD_REQUEST)

        booking.status = BookingStatus.CONFIRMED
        booking.save(update_fields=['status'])
        return Response({"status": booking.status}, status=drf_status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'])
    def reject(self, request, pk=None):
        """
        Отклонить бронь — доступно лендлорду объявления и админам.
        GET: подсказка. POST: меняет статус на REJECTED.
        """
        booking = self.get_object()
        user = request.user

        if request.method == 'GET':
            return Response({
                "detail": "Используйте POST для отклонения брони.",
                "current_status": booking.status
            })

        if not (self._is_admin(user) or self._is_landlord_of(user, booking)):
            return Response({"detail": "Недостаточно прав."}, status=drf_status.HTTP_403_FORBIDDEN)

        if booking.status in (BookingStatus.CANCELLED, BookingStatus.REJECTED):
            return Response({"detail": f"Бронь уже в статусе {booking.status}."},
                            status=drf_status.HTTP_400_BAD_REQUEST)

        booking.status = BookingStatus.REJECTED
        booking.save(update_fields=['status'])
        return Response({"status": booking.status}, status=drf_status.HTTP_200_OK)

    @action(detail=True, methods=['get', 'post'])
    def cancel(self, request, pk=None):
        """
        Отменить свою бронь — доступно арендатору этой брони и админам.
        Дедлайн контролируется настройкой BOOKING_CANCEL_DEADLINE_DAYS.
        GET: подсказка. POST: меняет статус на CANCELLED.
        """
        booking = self.get_object()
        user = request.user

        if request.method == 'GET':
            return Response({
                "detail": "Используйте POST для отмены брони.",
                "current_status": booking.status
            })

        # доступ только арендатору этой брони или админу
        if not (self._is_admin(user) or self._is_tenant_of(user, booking)):
            return Response({"detail": "Недостаточно прав."}, status=drf_status.HTTP_403_FORBIDDEN)

        # уже отменена/отклонена — дополнительные проверки
        if booking.status == BookingStatus.CANCELLED:
            return Response({"detail": "Бронь уже отменена."}, status=drf_status.HTTP_400_BAD_REQUEST)
        if booking.status == BookingStatus.REJECTED:
            return Response({"detail": "Бронь уже отклонена и не может быть отменена."},
                            status=drf_status.HTTP_400_BAD_REQUEST)

        # дедлайн: арендатор может отменить только до определённой даты
        # (админ — всегда)
        if not self._is_admin(user):
            today = timezone.localdate()  # т.к. у нас даты (без времени)
            deadline_days = getattr(settings, "BOOKING_CANCEL_DEADLINE_DAYS", 1)
            deadline_date = booking.start_date - datetime.timedelta(days=deadline_days)

            # запретить отмену в день заезда и позже
            if today >= booking.start_date:
                return Response(
                    {"detail": "Нельзя отменить бронь в день заезда или позже."},
                    status=drf_status.HTTP_400_BAD_REQUEST
                )

            # запретить, если позже дедлайна
            if today > deadline_date:
                msg = f"Отменить можно не позднее чем за {deadline_days} дн. до заезда (до {deadline_date})."
                return Response({"detail": msg}, status=drf_status.HTTP_400_BAD_REQUEST)

        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=['status'])
        return Response({"status": booking.status}, status=drf_status.HTTP_200_OK)
