from datetime import date

from django.contrib.auth.models import User
from django.db import models

from bookings.choices import BookingStatus
from listings.choices import ListingStatus
from .choices import UserRole


class UserProfile(models.Model):
    """
    Stores additional fields for a user (role, verification, etc.).
    One-to-one with the base Django `User` model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.TENANT,
        help_text='User role: tenant, landlord, or admin.',
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether KYC/verification has been passed. In production this should start as False; "
                  "an admin or automated process sets it to True after verification."
    )

    def __str__(self) -> str:
        return f"{self.user.username} — {self.get_role_display()}"

    def save(self, *args, **kwargs):
        # If the user is verified, force the role to LANDLORD.
        if self.is_verified and self.role != UserRole.LANDLORD:
            self.role = UserRole.LANDLORD
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class TenantManager(models.Manager):
    """Manager that limits the queryset to users with the TENANT role."""
    def get_queryset(self):
        return super().get_queryset().filter(profile__role=UserRole.TENANT)


class Tenant(User):
    """
    Proxy model over Django's `User` limited to users whose profile role is TENANT.
    No new table is created; this simply wraps the existing `auth_user` rows.
    """
    objects = TenantManager()

    class Meta:
        proxy = True
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def get_current_bookings(self):
        """
        Return confirmed bookings that have not yet ended (as of today).
        """
        return self.bookings.filter(
            status=BookingStatus.CONFIRMED,
            end_date__gte=date.today(),
        )


class LandlordManager(models.Manager):
    """Manager that limits the queryset to users with the LANDLORD role."""
    def get_queryset(self):
        return super().get_queryset().filter(profile__role=UserRole.LANDLORD)


class Landlord(User):
    """
    Proxy model over Django's `User` limited to users whose profile role is LANDLORD.
    """
    objects = LandlordManager()

    class Meta:
        proxy = True
        verbose_name = 'Landlord'
        verbose_name_plural = 'Landlords'

    def get_listings(self):
        """
        Return the landlord's active (AVAILABLE) listings.
        """
        return self.listings.filter(status=ListingStatus.AVAILABLE)
