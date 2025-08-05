from django.contrib.auth.models import User
from django.db import models

from bookings.choices import BookingStatus
from listings.choices import ListingStatus
from .choices import UserRole
from datetime import date


# UserProfile — хранилище для роли пользователя(User).
class UserProfile(models.Model):
    """
    User profile with additional fields.
    Linked one-to-one with the base User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.GUEST,
        help_text='User role: tenant, landlord, admin or guest'
    )

    def __str__(self) -> str:
        user: User = self.user  # type: ignore
        return f"{self.user.username} — {self.get_role_display()}"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


# За счёт своего менеджера (TenantManager) ты работаешь уже не со всеми пользователями, а только с арендаторами.
class TenantManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(profile__role=UserRole.TENANT)


class Tenant(User):
    """
    Создаёт прокси-модель на основе стандартного User, но только для тех пользователей,
    у которых в профиле стоит роль «tenant»
    """
    objects = TenantManager()

    class Meta:
        proxy = True                     # proxy = True не делает новую таблицу, а просто «оборачивает»
        verbose_name = 'Tenant'          # существующую. Все поля (username, email и т.д.) и поведения User остаются,
        verbose_name_plural = 'Tenants'  # но мы можем добавлять своё.

    def get_current_bookings(self):
        """
        Example method: returns confirmed bookings that have not ended as of today.
        """
        return self.bookings.filter(
            status=BookingStatus.CONFIRMED,
            end_date__gte=date.today()
        )


# # фильтрует пользователя по роли LANDLORD.
class LandlordManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(profile__role=UserRole.LANDLORD)


class Landlord(User):
    """
    Создаёт прокси-модель на основе стандартного User, но только для тех пользователей,
    у которых в профиле стоит роль «landlord»
    """
    objects = LandlordManager()

    class Meta:
        proxy = True
        verbose_name = 'Landlord'
        verbose_name_plural = 'Landlords'

    def get_listings(self):
        """
        Returns the landlord's active listings.
        """
        return self.listings.filter(status=ListingStatus.AVAILABLE)
