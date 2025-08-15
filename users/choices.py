from django.db import models


class UserRole(models.TextChoices):
    TENANT = 'tenant', 'Tenant'
    LANDLORD = 'landlord', 'Landlord'
    ADMIN = 'admin', 'Admin'
