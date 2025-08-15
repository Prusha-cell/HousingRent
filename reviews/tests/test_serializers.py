import pytest
from datetime import date, timedelta
from model_bakery import baker
from rest_framework.test import APIRequestFactory
from reviews.serializers import ReviewSerializer


@pytest.fixture
def rf():
    return APIRequestFactory()


def make_serializer_for(user, data, instance=None, method="POST"):
    req = APIRequestFactory().post("/") if method == "POST" else APIRequestFactory().patch("/")
    req.user = user
    ctx = {"request": req}
    return ReviewSerializer(instance=instance, data=data, context=ctx, partial=(method == "PATCH"))


@pytest.mark.django_db
def test_serializer_ok(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    # completed & confirmed booking
    b = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tt,
        start_date=date.today() - timedelta(days=5),
        end_date=date.today() - timedelta(days=2),
        status="confirmed",
    )
    ser = make_serializer_for(tt, {"booking": b.id, "rating": 5, "comment": "ok"})
    assert ser.is_valid(), ser.errors
    obj = ser.save()
    assert obj.listing_id == listing.id
    assert obj.tenant_id == tt.id
    assert obj.booking_id == b.id


@pytest.mark.django_db
def test_serializer_rejects_landlord_himself(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    # owner is (incorrectly) the tenant as well
    b = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=ll,
        start_date=date.today() - timedelta(days=5),
        end_date=date.today() - timedelta(days=2),
        status="confirmed",
    )
    ser = make_serializer_for(ll, {"booking": b.id, "rating": 4, "comment": "no"})
    assert not ser.is_valid()


@pytest.mark.django_db
def test_serializer_rejects_foreign_booking(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    t1 = user_with_profile(username="t1", role="tenant")
    t2 = user_with_profile(username="t2", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    b = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=t1,
        start_date=date.today() - timedelta(days=5),
        end_date=date.today() - timedelta(days=2),
        status="confirmed",
    )
    ser = make_serializer_for(t2, {"booking": b.id, "rating": 4})
    assert not ser.is_valid()


@pytest.mark.django_db
def test_serializer_requires_confirmed_and_finished(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")

    # pending — not allowed
    b_pending = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tt,
        start_date=date.today() - timedelta(days=5),
        end_date=date.today() - timedelta(days=2),
        status="pending",
    )
    ser1 = make_serializer_for(tt, {"booking": b_pending.id, "rating": 3})
    assert not ser1.is_valid()

    # confirmed but not finished yet — not allowed
    b_future = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tt,
        start_date=date.today() + timedelta(days=1),
        end_date=date.today() + timedelta(days=2),
        status="confirmed",
    )
    ser2 = make_serializer_for(tt, {"booking": b_future.id, "rating": 3})
    assert not ser2.is_valid()


@pytest.mark.django_db
def test_serializer_prevents_duplicate_and_change_booking(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    b = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tt,
        start_date=date.today() - timedelta(days=5),
        end_date=date.today() - timedelta(days=2),
        status="confirmed",
    )

    # first is OK
    s1 = make_serializer_for(tt, {"booking": b.id, "rating": 5})
    assert s1.is_valid()
    r1 = s1.save()

    # a second review for the same booking — not allowed
    s2 = make_serializer_for(tt, {"booking": b.id, "rating": 4})
    assert not s2.is_valid()

    # on update you cannot change the booking
    s3 = make_serializer_for(tt, {"booking": b.id, "rating": 2}, instance=r1, method="PATCH")
    assert s3.is_valid()
    other_b = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tt,
        start_date=date.today() - timedelta(days=10),
        end_date=date.today() - timedelta(days=7),
        status="confirmed",
    )
    s4 = make_serializer_for(tt, {"booking": other_b.id}, instance=r1, method="PATCH")
    assert not s4.is_valid()
