from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from listings.models import Listing


class SearchHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_history',
        help_text="User who made the search"
    )
    keyword = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} searched '{self.keyword}'"

    class Meta:
        verbose_name = 'Search History'
        verbose_name_plural = 'Search Histories'
        ordering = ['-searched_at']


class ListingView(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='listing_views',
        help_text="User who viewed the listing"
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='views',
        help_text="The listing being viewed"
    )
    viewed_at = models.DateTimeField(auto_now=True)
    viewed_on = models.DateField(default=timezone.localdate, db_index=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} viewed {self.listing.title}"

    class Meta:
        verbose_name = 'Listing View'
        verbose_name_plural = 'Listing Views'
        ordering = ['-viewed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'listing', 'viewed_on'],
                name='uniq_listing_view_per_user_per_day'
            )
        ]
