from django.db import models


class UserRole(models.TextChoices):
    GUEST = 'guest', 'Guest'              # guest - отображение в коде
    TENANT = 'tenant', 'Tenant'           # Guest - отображение в админке
    LANDLORD = 'landlord', 'Landlord'
