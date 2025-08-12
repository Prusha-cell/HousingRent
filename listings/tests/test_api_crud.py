import pytest
from model_bakery import baker
from listings.models import Listing

BASE = "/api/listings/"
LIST_URL = f"{BASE}listings/"        # публичный read-only
MY_URL   = f"{BASE}my-listings/"     # CRUD для владельца


@pytest.mark.django_db
def test_listings_list_anonymous_ok(api_client):
    baker.make("listings.Listing", status="available")
    resp = api_client.get(LIST_URL)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.django_db
def test_listings_create_landlord_only(api_client, user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")  # verified не требуется по твоим пермишенам
    api_client.force_authenticate(user=ll)

    payload = {
        "title": "Nice flat",
        "description": "Sunny and cozy",
        "location_city": "Odessa",
        "location_district": "Malinovsky",
        "price": "1200.00",
        "rooms": 2,
        "housing_type": "apartment",
        "status": "available",
    }
    resp = api_client.post(MY_URL, payload, format="json")   # <— ВАЖНО: my-listings
    assert resp.status_code in (201, 200)

    obj_id = resp.json().get("id") or Listing.objects.latest("id").id
    # владелец действительно текущий пользователь
    listing_db = Listing.objects.get(id=obj_id)
    assert listing_db.landlord_id == ll.id


@pytest.mark.django_db
def test_listings_create_tenant_forbidden(api_client, user_with_profile):
    tenant = user_with_profile(username="tt", role="tenant")
    api_client.force_authenticate(user=tenant)

    payload = {
        "title": "Should fail",
        "description": "nope",
        "location_city": "Kyiv",
        "location_district": "Center",
        "price": "900.00",
        "rooms": 1,
        "housing_type": "studio",
        "status": "available",
    }
    resp = api_client.post(MY_URL, payload, format="json")
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_listings_update_only_owner(api_client, user_with_profile):
    owner = user_with_profile(username="owner1", role="landlord")
    other = user_with_profile(username="intruder", role="landlord")

    listing = baker.make(
        "listings.Listing",
        landlord=owner,
        title="Old title",
        description="x",
        location_city="Dnipro",
        location_district="South",
        price="1000.00",
        rooms=2,
        housing_type="apartment",
        status="available",
    )

    detail_my = f"{MY_URL}{listing.id}/"

    # чужой — увидит 404 (его queryset не содержит этот объект)
    api_client.force_authenticate(user=other)
    resp_forbidden = api_client.patch(detail_my, {"title": "Hacked"}, format="json")
    assert resp_forbidden.status_code == 404

    # владелец — можно
    api_client.force_authenticate(user=owner)
    resp_ok = api_client.patch(detail_my, {"title": "New title"}, format="json")
    assert resp_ok.status_code in (200, 202)
    listing.refresh_from_db()
    assert listing.title == "New title"


@pytest.mark.django_db
def test_listings_delete_only_owner(api_client, user_with_profile):
    owner = user_with_profile(username="owner2", role="landlord")
    other = user_with_profile(username="intruder2", role="landlord")

    listing = baker.make(
        "listings.Listing",
        landlord=owner,
        title="To be deleted",
        description="x",
        location_city="Uman",
        location_district="Central",
        price="800.00",
        rooms=1,
        housing_type="house",
        status="available",
    )

    detail_my = f"{MY_URL}{listing.id}/"

    api_client.force_authenticate(user=other)
    r1 = api_client.delete(detail_my)
    assert r1.status_code == 404

    api_client.force_authenticate(user=owner)
    r2 = api_client.delete(detail_my)
    assert r2.status_code in (200, 202, 204)
