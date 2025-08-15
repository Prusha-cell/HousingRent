from django.db import models
from django.contrib.auth.models import User


from bookings.models import Booking
from listings.models import Listing
from reviews.choices import ReviewRating


class Review(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text="The listing being reviewed"
    )
    tenant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        help_text="Tenant who leaves the review"
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name='reviews',
        help_text='One review per booking')
    rating = models.PositiveSmallIntegerField(
        choices=ReviewRating.choices,
        default=ReviewRating.THREE,
        help_text="Rating from 1 (Poor) to 5 (Excellent)"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.username}'s review for {self.listing.title} ({self.rating})"

    class Meta:
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'booking'],
                name='one_review_per_booking',
            )
        ]
