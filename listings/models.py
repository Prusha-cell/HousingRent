from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from users.choices import UserRole
from .choices import HousingType, ListingStatus


class Listing(models.Model):
    landlord = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listings',
        help_text="Landlord who owns this listing"
    )
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    location_city = models.CharField(max_length=100)
    location_district = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8,
                                decimal_places=2,
                                validators=[MinValueValidator(0)],
                                help_text='for example: 199.99',
                                )
    rooms = models.PositiveIntegerField(default=1, help_text='Number of rooms in the property')
    housing_type = models.CharField(max_length=30,
                                    choices=HousingType.choices,
                                    default=HousingType.APARTMENT
                                    )
    status = models.CharField(
        max_length=20,
        choices=ListingStatus.choices,
        default=ListingStatus.AVAILABLE,
        help_text='Status for apartment',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    views_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.location_city}, {self.price}€)"

    class Meta:
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'
        ordering = ['-created_at']
