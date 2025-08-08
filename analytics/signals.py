from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from .models import ListingView
from listings.models import Listing


@receiver(post_save, sender=ListingView)
def inc_listing_views(sender, instance, created, **kwargs):
    if created:
        Listing.objects.filter(pk=instance.listing_id).update(views_count=F('views_count') + 1)
