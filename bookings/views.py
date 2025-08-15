from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from rest_framework import viewsets, permissions, status as drf_status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from listings.models import Listing
from .choices import BookingStatus
from .models import Booking
from .serializers import BookingSerializer
from utils.permissions import IsBookingActorOrAdmin


class BookingViewSet(viewsets.ModelViewSet):
    """
    CRUD + actions for bookings.

    Visibility (get_queryset):
      - Admin/staff: all bookings.
      - Regular user: own bookings OR bookings for listings they own (landlord).
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsBookingActorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = Booking.objects.select_related("listing")
        if user.is_staff or user.is_superuser:
            return qs
        # Non-admins: see (a) own bookings, (b) bookings for their listings
        return qs.filter(
            Q(tenant_id=user.pk) | Q(listing__landlord_id=user.pk)
        ).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        listing = serializer.validated_data["listing"]

        # A landlord cannot book their own listing
        if listing.landlord_id == user.pk:
            raise ValidationError({"detail": "You cannot book your own listing."})

        # Concurrency guard: lock the listing row while saving the booking
        # (SQLite: no-op; MySQL/Postgres: proper row-level lock)
        with transaction.atomic():
            Listing.objects.select_for_update().get(pk=listing.pk)
            serializer.save(tenant=user)

    def perform_update(self, serializer):
        # Lock the related listing to avoid race conditions while updating
        with transaction.atomic():
            listing = serializer.validated_data.get("listing") or serializer.instance.listing
            Listing.objects.select_for_update().get(pk=listing.pk)
            serializer.save()

    # ----------------- helpers -----------------

    def _is_admin(self, user):
        return user.is_staff or user.is_superuser

    def _is_landlord_of(self, user, booking):
        return getattr(booking.listing, "landlord_id", None) == user.pk

    def _is_tenant_of(self, user, booking):
        return getattr(booking, "tenant_id", None) == user.pk

    # ----------------- actions -----------------

    @action(detail=True, methods=["get", "post"])
    def confirm(self, request, pk=None):
        """
        Confirm a booking — allowed for the listing's landlord or admins.
        GET: hint message. POST: changes status to CONFIRMED.
        """
        booking = self.get_object()
        user = request.user

        if request.method == "GET":
            return Response({
                "detail": "Use POST to confirm the booking.",
                "current_status": booking.status,
            })

        if not (self._is_admin(user) or self._is_landlord_of(user, booking)):
            return Response({"detail": "Insufficient permissions."}, status=drf_status.HTTP_403_FORBIDDEN)

        # Only pending bookings can be confirmed
        if booking.status != BookingStatus.PENDING:
            return Response(
                {"detail": "Only bookings with status 'pending' can be confirmed."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        booking.status = BookingStatus.CONFIRMED
        booking.save(update_fields=["status"])
        return Response({"status": BookingStatus.CONFIRMED},
                        status=drf_status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Cancel a booking.
        Allowed for: admin/staff, tenant (owner of booking), or landlord of the listing.
        """
        booking = self.get_object()
        user = request.user


        is_admin = user.is_staff or user.is_superuser
        is_tenant = getattr(booking, "tenant_id", None) == user.pk
        is_landlord = getattr(booking.listing, "landlord_id", None) == user.pk
        if not (is_admin or is_tenant or is_landlord):
            return Response({"detail": "Insufficient permissions."}, status=drf_status.HTTP_403_FORBIDDEN)

        # cannot be cancelled retroactively / after the start
        today = timezone.localdate()
        if booking.start_date <= today:
            return Response({"detail": "Booking has already started; cannot cancel."},
                            status=drf_status.HTTP_400_BAD_REQUEST)

        # check the current status
        if booking.status == BookingStatus.CANCELLED:
            return Response({"detail": "Booking is already canceled."},
                            status=drf_status.HTTP_400_BAD_REQUEST)

        # (opt.) prohibition on cancellation of CONFIRMED by ordinary tenant:
        if booking.status == BookingStatus.CONFIRMED and not (is_admin or is_landlord):
            return Response({"detail": "Only landlord or admin can cancel a confirmed booking."},
                            status=drf_status.HTTP_403_FORBIDDEN)

        deadline = getattr(settings, "BOOKING_CANCEL_DEADLINE_DAYS", 0)
        days_to_start = (booking.start_date - today).days
        # We block if there are LESS than the deadline days left
        if days_to_start < deadline:
            return Response(
                {"detail": f"Too late to cancel. Deadline is {deadline} day(s) before check-in."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=["status"])
        return Response({"detail": "Booking canceled.", "status": booking.status})

    @action(detail=True, methods=['get', 'post'])
    def reject(self, request, pk=None):
        """
        Reject a booking — allowed for the listing's landlord or admins.
        Only 'pending' bookings can be rejected.
        GET: hint message. POST: changes status to REJECT.
        """
        booking = self.get_object()
        user = request.user

        if request.method == 'GET':
            return Response({"detail": "Use POST to REJECT the booking.",
                             "current_status": booking.status})

        if not (self._is_admin(user) or self._is_landlord_of(user, booking)):
            return Response(
                {'detail': 'Insufficient permissions.'},
                status=drf_status.HTTP_403_FORBIDDEN
            )

        if booking.status != BookingStatus.PENDING:
            return Response(
                {
                    'detail': 'Only bookings with status PENDING can be REJECTED.',
                    'current_status': booking.status
                },
                status=drf_status.HTTP_400_BAD_REQUEST
            )

        booking.status = BookingStatus.REJECTED
        booking.save(update_fields=['status'])

        return Response(
            {'detail': BookingStatus.REJECTED},
            status=drf_status.HTTP_200_OK
        )
