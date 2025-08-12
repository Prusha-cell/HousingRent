import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_signal_inc_views_count(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    listing = baker.make("listings.Listing", landlord=ll, views_count=5)

    # создание ListingView должно +1 к счётчику
    baker.make("analytics.ListingView", user=ll, listing=listing)
    listing.refresh_from_db()
    assert listing.views_count == 6
