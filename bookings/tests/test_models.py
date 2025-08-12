import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_booking_str(user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    tenant = user_with_profile(username="tt", role="tenant")

    listing = baker.make(
        "listings.Listing",
        landlord=landlord,
        title="Flat A",
        description="x",
        location_city="Kyiv",
        location_district="Center",
        price="1000.00",
        rooms=2,
        housing_type="apartment",
        status="available",
    )

    bk = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tenant,
        start_date="2099-01-10",
        end_date="2099-01-12",
        status="pending",
    )
    s = str(bk)
    assert "Booking by tt for Flat A" in s
    assert "[2099-01-10 - 2099-01-12]" in s
