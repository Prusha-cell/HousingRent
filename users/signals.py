from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance, created, **kwargs):
    """
    Ensure a profile exists for every user.

    Create a UserProfile only when the user is first created.
    If a profile already exists for any reason, do nothing.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
