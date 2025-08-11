from django.db import models


class BookingStatus(models.TextChoices):
    REJECTED = 'rejected', 'Rejected'
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELLED = 'cancelled', 'Cancelled'

