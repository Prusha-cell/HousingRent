import pytest
from model_bakery import baker

BASE = "/api/listings/"
MY_URL = f"{BASE}my-listings/"


@pytest.mark.django_db
def test_my_listings_forbidden_for_tenant(api_client, user_with_profile):
    tenant = user_with_profile(username="ten", role="tenant")
    api_client.force_authenticate(user=tenant)

    resp = api_client.get(MY_URL)
    assert resp.status_code in (401, 403)


@pytest.mark.django_db
def test_my_listings_returns_only_owners_objects(api_client, user_with_profile):
    owner = user_with_profile(username="own", role="landlord")
    other = user_with_profile(username="oth", role="landlord")

    mine = baker.make("listings.Listing", landlord=owner, _quantity=2, status="available")
    baker.make("listings.Listing", landlord=other, _quantity=3, status="available")

    api_client.force_authenticate(user=owner)
    resp = api_client.get(MY_URL)
    assert resp.status_code == 200

    data = resp.json()

    returned_ids = {item["id"] for item in data["results"]}
    expected_ids = {obj.id for obj in mine}
    assert returned_ids == expected_ids
