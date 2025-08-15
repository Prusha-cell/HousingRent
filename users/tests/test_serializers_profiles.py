from datetime import date, timedelta

import pytest
from django.contrib.auth.models import User
from model_bakery import baker

from users.models import Tenant, Landlord, UserProfile
from users.serializers.profiles import TenantSerializer, LandlordSerializer
from users.serializers.admin_user import AdminUserWriteSerializer


@pytest.mark.django_db
def test_tenant_serializer_basic(user_with_profile):
    # create a user with the tenant role
    user = user_with_profile(username="ten", role="tenant", email="ten@ex.com")
    # the Tenant proxy points to the same user (by pk)
    tenant = Tenant.objects.get(pk=user.pk)

    ser = TenantSerializer(tenant)
    data = ser.data

    assert data["username"] == "ten"
    assert data["email"] == "ten@ex.com"
    # no bookings yet — should be an empty list
    assert isinstance(data.get("current_bookings"), list)
    assert data["current_bookings"] == []


@pytest.mark.django_db
def test_landlord_serializer_basic(user_with_profile):
    # create a user with the landlord role
    user = user_with_profile(username="ll", role="landlord", email="ll@ex.com")
    landlord = Landlord.objects.get(pk=user.pk)

    ser = LandlordSerializer(landlord)
    data = ser.data

    assert data["username"] == "ll"
    assert data["email"] == "ll@ex.com"
    # no active listings yet — should be an empty list
    assert isinstance(data.get("active_listings"), list)
    assert data["active_listings"] == []


@pytest.mark.django_db
def test_landlord_serializer_after_admin_create():
    """
    Integration test: create a user via AdminUserWriteSerializer with profile.role='landlord'.
    Verify that:
      1) the password is hashed,
      2) the profile is created and the role is stored,
      3) the Landlord proxy works and can be serialized.
    """
    payload = {
        "username": "from_admin",
        "email": "fa@ex.com",
        "first_name": "From",
        "last_name": "Admin",
        "password": "fromadmin123",
        "is_active": True,
        "is_staff": False,
        "profile": {"role": "landlord"},
    }
    ser = AdminUserWriteSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    user = ser.save()

    # password is set
    assert isinstance(user, User)
    assert user.check_password("fromadmin123")

    # role was updated via direct update() -> refresh from DB and re-read profile
    user.refresh_from_db()
    # ensure profile exists and has the correct role
    profile = UserProfile.objects.get(user=user)
    assert profile.role == "landlord"

    # the proxy model should “see” this user
    landlord = Landlord.objects.get(pk=user.pk)

    ser2 = LandlordSerializer(landlord)
    data = ser2.data
    assert data["username"] == "from_admin"
    assert data["email"] == "fa@ex.com"
    assert data["active_listings"] == []


@pytest.mark.django_db
def test_tenant_serializer_current_bookings_populated(user_with_profile):
    # tenant + landlord
    tenant_user = user_with_profile(username="tenant1", role="tenant", email="t1@ex.com")
    landlord_user = user_with_profile(username="landlord1", role="landlord", email="l1@ex.com")

    # a listing owned by landlord
    listing = baker.make(
        "listings.Listing",
        landlord=landlord_user,
        title="Apt 101",
        description="Nice",
        location_city="Odessa",
        location_district="Malinovsky",
        price="1000.00",
        rooms=2,
        housing_type="apartment",
        status="available",
    )

    # a “current” booking for the tenant (ensure it falls into the selection)
    baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tenant_user,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=2),
        status="confirmed",
    )

    tenant = Tenant.objects.get(pk=tenant_user.pk)
    data = TenantSerializer(tenant).data

    # base fields
    assert data["username"] == "tenant1"
    assert data["email"] == "t1@ex.com"

    # check that current_bookings is non-empty
    assert isinstance(data.get("current_bookings"), list)
    assert len(data["current_bookings"]) == 1


@pytest.mark.django_db
def test_landlord_serializer_active_listings_populated(user_with_profile):
    landlord_user = user_with_profile(username="landlord2", role="landlord", email="l2@ex.com")

    # two listings: one available and one unavailable
    baker.make(
        "listings.Listing",
        landlord=landlord_user,
        title="Avail 1",
        description="x",
        location_city="Kyiv",
        location_district="Center",
        price="1500.00",
        rooms=3,
        housing_type="apartment",
        status="available",
    )
    baker.make(
        "listings.Listing",
        landlord=landlord_user,
        title="Hidden 1",
        description="x",
        location_city="Kyiv",
        location_district="Center",
        price="1500.00",
        rooms=3,
        housing_type="apartment",
        status="unavailable",
    )

    landlord = Landlord.objects.get(pk=landlord_user.pk)
    data = LandlordSerializer(landlord).data

    # base fields
    assert data["username"] == "landlord2"
    assert data["email"] == "l2@ex.com"

    # expect only “active” listings to be returned
    assert isinstance(data.get("active_listings"), list)
    assert len(data["active_listings"]) == 1
