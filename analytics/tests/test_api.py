import pytest
from model_bakery import baker

BASE = "/api/analytics/"
SEARCH_URL = f"{BASE}search-history/"
VIEWS_URL = f"{BASE}listing-views/"


# ---- SearchHistory ----

@pytest.mark.django_db
def test_search_history_create_and_list_scope(api_client, user_with_profile):
    u1 = user_with_profile(username="u1", role="tenant")
    u2 = user_with_profile(username="u2", role="tenant")

    # u1 создаёт две записи
    api_client.force_authenticate(user=u1)
    r1 = api_client.post(SEARCH_URL, {"keyword": "odessa"}, format="json")
    r2 = api_client.post(SEARCH_URL, {"keyword": "kyiv"}, format="json")
    assert r1.status_code in (200, 201)
    assert r2.status_code in (200, 201)

    # u2 создаёт одну запись
    api_client.force_authenticate(user=u2)
    r3 = api_client.post(SEARCH_URL, {"keyword": "dnipro"}, format="json")
    assert r3.status_code in (200, 201)

    # u1 видит только свои 2
    api_client.force_authenticate(user=u1)
    list_u1 = api_client.get(SEARCH_URL)
    assert list_u1.status_code == 200
    data_u1 = list_u1.json()
    assert isinstance(data_u1, list)
    assert len(data_u1) == 2
    assert {item["keyword"] for item in data_u1} == {"odessa", "kyiv"}


@pytest.mark.django_db
def test_search_history_requires_auth(api_client):
    r = api_client.get(SEARCH_URL)
    assert r.status_code in (401, 403)
    r2 = api_client.post(SEARCH_URL, {"keyword": "x"}, format="json")
    assert r2.status_code in (401, 403)


@pytest.mark.django_db
def test_search_history_hidden_user_is_ignored(api_client, user_with_profile):
    u1 = user_with_profile(username="u1", role="tenant")
    u2 = user_with_profile(username="u2", role="tenant")

    # даже если клиент пытается подставить чужой user — HiddenField перетрёт на request.user
    api_client.force_authenticate(user=u1)
    r = api_client.post(SEARCH_URL, {"keyword": "try", "user": u2.id}, format="json")
    assert r.status_code in (200, 201)
    assert r.json()["keyword"] == "try"
    # и при чтении вернётся запись с user = u1
    lst = api_client.get(SEARCH_URL).json()
    assert len(lst) == 1 and lst[0]["keyword"] == "try"


# ---- ListingView ----

@pytest.mark.django_db
def test_listing_view_create_and_list_scope(api_client, user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    u1 = user_with_profile(username="u1", role="tenant")
    u2 = user_with_profile(username="u2", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll)

    # u1 создаёт 2 просмотра
    api_client.force_authenticate(user=u1)
    assert api_client.post(VIEWS_URL, {"listing": listing.id}, format="json").status_code in (200, 201)
    assert api_client.post(VIEWS_URL, {"listing": listing.id}, format="json").status_code in (200, 201)

    # u2 создаёт 1 просмотр
    api_client.force_authenticate(user=u2)
    assert api_client.post(VIEWS_URL, {"listing": listing.id}, format="json").status_code in (200, 201)

    # u1 видит только свои 2
    api_client.force_authenticate(user=u1)
    res = api_client.get(VIEWS_URL)
    assert res.status_code == 200
    assert len(res.json()) == 2


@pytest.mark.django_db
def test_listing_view_requires_auth(api_client):
    r = api_client.get(VIEWS_URL)
    assert r.status_code in (401, 403)
    r2 = api_client.post(VIEWS_URL, {"listing": 1}, format="json")
    assert r2.status_code in (401, 403)


@pytest.mark.django_db
def test_listing_view_hidden_user_is_ignored_and_signal_increments(api_client, user_with_profile):
    # проверим, что user в payload игнорируется (HiddenField) и сигнал увеличивает views_count
    ll = user_with_profile(username="ll", role="landlord")
    u1 = user_with_profile(username="u1", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, views_count=0)

    api_client.force_authenticate(user=u1)
    r = api_client.post(VIEWS_URL, {"listing": listing.id, "user": ll.id}, format="json")
    assert r.status_code in (200, 201)

    # сигнал post_save должен был инкрементить
    listing.refresh_from_db()
    assert listing.views_count == 1
