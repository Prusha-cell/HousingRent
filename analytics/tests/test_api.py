import pytest
from model_bakery import baker
from freezegun import freeze_time

BASE = "/api/analytics/"
SEARCH_URL = f"{BASE}search-history/"
VIEWS_URL = f"{BASE}listing-views/"


# ---- SearchHistory ----

@pytest.mark.django_db
def test_search_history_create_and_list_scope(api_client, user_with_profile):
    """User should see only their own search history entries."""
    u1 = user_with_profile(username="u1", role="tenant")
    u2 = user_with_profile(username="u2", role="tenant")

    # u1 creates two entries
    api_client.force_authenticate(user=u1)
    r1 = api_client.post(SEARCH_URL, {"keyword": "odessa"}, format="json")
    r2 = api_client.post(SEARCH_URL, {"keyword": "kyiv"}, format="json")
    assert r1.status_code in (200, 201)
    assert r2.status_code in (200, 201)

    # u2 creates one entry
    api_client.force_authenticate(user=u2)
    r3 = api_client.post(SEARCH_URL, {"keyword": "dnipro"}, format="json")
    assert r3.status_code in (200, 201)

    # u1 should see only their two entries
    api_client.force_authenticate(user=u1)
    list_u1 = api_client.get(SEARCH_URL)
    assert list_u1.status_code == 200
    data_u1 = list_u1.json()
    assert data_u1["count"] == 2
    items = data_u1["results"]
    assert isinstance(items, list)
    assert len(items) == 2
    assert {item["keyword"] for item in items} == {"odessa", "kyiv"}


@pytest.mark.django_db
def test_search_history_requires_auth(api_client):
    """Listing and creating search history require authentication."""
    r = api_client.get(SEARCH_URL)
    assert r.status_code in (401, 403)
    r2 = api_client.post(SEARCH_URL, {"keyword": "x"}, format="json")
    assert r2.status_code in (401, 403)


@pytest.mark.django_db
def test_search_history_hidden_user_is_ignored(api_client, user_with_profile):
    """
    Even if the client sends someone else's 'user' in payload,
    HiddenField must override it with request.user.
    """
    u1 = user_with_profile(username="u1", role="tenant")
    u2 = user_with_profile(username="u2", role="tenant")

    api_client.force_authenticate(user=u1)
    r = api_client.post(SEARCH_URL, {"keyword": "try", "user": u2.id}, format="json")
    assert r.status_code in (200, 201)
    assert r.json()["keyword"] == "try"

    # Reading should return the record bound to u1
    lst = api_client.get(SEARCH_URL).json()
    assert lst["count"] == 1
    assert lst["results"][0]["keyword"] == "try"


# ---- ListingView ----

@freeze_time("2025-08-24 10:00:00")
@pytest.mark.django_db
def test_listing_view_create_and_list_scope(api_client, user_with_profile):
    """User should see only their own listing-view events."""
    ll = user_with_profile(username="ll", role="landlord")
    u1 = user_with_profile(username="u1", role="tenant")
    u2 = user_with_profile(username="u2", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll)

    # u1 creates 2 views
    api_client.force_authenticate(user=u1)
    assert api_client.post(VIEWS_URL, {"listing": listing.id}, format="json").status_code in (200, 201)
    assert api_client.post(VIEWS_URL, {"listing": listing.id}, format="json").status_code in (200, 201)

    # u2 creates 1 view
    api_client.force_authenticate(user=u2)
    assert api_client.post(VIEWS_URL, {"listing": listing.id}, format="json").status_code in (200, 201)

    # u1 should see only their 2 views
    api_client.force_authenticate(user=u1)
    res = api_client.get(VIEWS_URL)
    assert res.status_code == 200
    # в тот же день — одна запись
    assert res.json()["count"] == 1
    # следующий день → вторая запись для u1
    with freeze_time("2025-08-25 09:00:00"):
        assert api_client.post(VIEWS_URL, {"listing": listing.id}, format="json").status_code in (200, 201)
        res = api_client.get(VIEWS_URL)
        assert res.status_code == 200
        assert res.json()["count"] == 2


@pytest.mark.django_db
def test_listing_view_requires_auth(api_client):
    """Listing and creating listing views require authentication."""
    r = api_client.get(VIEWS_URL)
    assert r.status_code in (401, 403)
    r2 = api_client.post(VIEWS_URL, {"listing": 1}, format="json")
    assert r2.status_code in (401, 403)


@pytest.mark.django_db
def test_listing_view_hidden_user_is_ignored_and_signal_increments(api_client, user_with_profile):
    """
    'user' field in payload must be ignored (HiddenField), and the signal should
    increment Listing.views_count on create.
    """
    ll = user_with_profile(username="ll", role="landlord")
    u1 = user_with_profile(username="u1", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, views_count=0)

    api_client.force_authenticate(user=u1)
    r = api_client.post(VIEWS_URL, {"listing": listing.id, "user": ll.id}, format="json")
    assert r.status_code in (200, 201)

    # post_save signal should increment views_count
    listing.refresh_from_db()
    assert listing.views_count == 1
