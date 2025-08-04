from rest_framework import viewsets
from .serializers import BookingSerializer
from bookings.models import Booking


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
