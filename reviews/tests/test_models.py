import pytest
from model_bakery import baker
from django.db import IntegrityError


@pytest.mark.django_db
def test_review_str(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")

    listing = baker.make(
        "listings.Listing",
        landlord=ll,
        title="Flat A",
        status="available",
    )
    booking = baker.make(
        "bookings.Booking",
        listing=listing,
        tenant=tt,
        start_date="2099-01-01",
        end_date="2099-01-03",
        status="confirmed",
    )
    review = baker.make(
        "reviews.Review",
        listing=listing,
        tenant=tt,
        booking=booking,
        rating=5,
        comment="great",
    )
    s = str(review)
    assert "tt's review for Flat A" in s
    assert "(5)" in s


@pytest.mark.django_db
def test_one_review_per_booking_unique(user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    booking = baker.make("bookings.Booking", listing=listing, tenant=tt,
                         start_date="2099-01-01", end_date="2099-01-03", status="confirmed")

    baker.make("reviews.Review", listing=listing, tenant=tt, booking=booking, rating=4)

    with pytest.raises(IntegrityError):
        baker.make("reviews.Review", listing=listing, tenant=tt, booking=booking, rating=3)
