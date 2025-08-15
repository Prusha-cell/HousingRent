import pytest
from datetime import date, timedelta
from model_bakery import baker
from bookings.serializers import BookingSerializer
from bookings.models import Booking
from listings.choices import ListingStatus


@pytest.mark.django_db
def test_serializer_valid_ok(user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    tenant = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.AVAILABLE)

    d1 = date.today() + timedelta(days=5)
    d2 = d1 + timedelta(days=2)

    ser = BookingSerializer(data={"listing": listing.id, "start_date": d1, "end_date": d2})
    ser.is_valid(raise_exception=True)  # should not raise


@pytest.mark.django_db
def test_serializer_reject_unavailable_listing(user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    tenant = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.UNAVAILABLE)

    d1 = date.today() + timedelta(days=5)
    d2 = d1 + timedelta(days=2)

    ser = BookingSerializer(data={"listing": listing.id, "start_date": d1, "end_date": d2})
    assert not ser.is_valid()
    # error message should indicate the listing is unavailable
    err_text = str(ser.errors).lower()
    assert ("unavailable" in err_text) or ("not available" in err_text)


@pytest.mark.django_db
def test_serializer_dates_and_overlap(user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    tenant1 = user_with_profile(username="t1", role="tenant")
    tenant2 = user_with_profile(username="t2", role="tenant")
    listing = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.AVAILABLE)

    today = date.today()

    # past start date -> invalid
    ser_bad_past = BookingSerializer(
        data={"listing": listing.id, "start_date": today - timedelta(days=1), "end_date": today + timedelta(days=2)}
    )
    assert not ser_bad_past.is_valid()

    # start >= end -> invalid
    d = today + timedelta(days=7)
    ser_bad_order = BookingSerializer(data={"listing": listing.id, "start_date": d, "end_date": d})
    assert not ser_bad_order.is_valid()

    # valid reference booking
    a1 = today + timedelta(days=10)
    a2 = a1 + timedelta(days=3)
    b1 = Booking.objects.create(
        listing=listing, tenant=tenant1, start_date=a1, end_date=a2, status="confirmed"
    )

    # overlapping dates -> invalid
    ser_overlap = BookingSerializer(
        data={"listing": listing.id, "start_date": a1 + timedelta(days=1), "end_date": a2 + timedelta(days=1)}
    )
    assert not ser_overlap.is_valid()
