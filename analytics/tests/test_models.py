import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_search_history_str_and_auto_timestamp(user_with_profile):
    u = user_with_profile(username="u1", role="tenant")
    sh = baker.make("analytics.SearchHistory", user=u, keyword="odessa")
    assert "u1" in str(sh)
    assert "odessa" in str(sh)
    assert sh.searched_at is not None  # auto_now_add


@pytest.mark.django_db
def test_listing_view_str_and_auto_timestamp(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    l = baker.make("listings.Listing", landlord=ll, title="Flat A")
    v = baker.make("analytics.ListingView", user=ll, listing=l)
    assert "ll" in str(v)
    assert "Flat A" in str(v)
    assert v.viewed_at is not None  # auto_now_add
