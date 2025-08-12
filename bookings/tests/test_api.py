import pytest
from datetime import date, timedelta
from model_bakery import baker
from bookings.models import Booking
from listings.choices import ListingStatus

BASE = "/api/bookings/"


@pytest.mark.django_db
def test_create_booking_success(api_client, user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    tenant = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.AVAILABLE)

    api_client.force_authenticate(user=tenant)
    d1 = date.today() + timedelta(days=5)
    d2 = d1 + timedelta(days=2)
    payload = {"listing": listing.id, "start_date": d1, "end_date": d2}

    r = api_client.post(BASE, payload, format="json")
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["status"] == "pending"
    assert data["tenant"] == tenant.id


@pytest.mark.django_db
def test_cannot_book_own_listing(api_client, user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    listing = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.AVAILABLE)

    api_client.force_authenticate(user=landlord)
    d1 = date.today() + timedelta(days=5)
    d2 = d1 + timedelta(days=2)
    r = api_client.post(BASE, {"listing": listing.id, "start_date": d1, "end_date": d2}, format="json")
    # perform_create поднимает ValidationError -> 400
    assert r.status_code == 400
    assert "нельзя бронировать" in r.json().get("detail", "").lower() or "нельзя бронировать" in str(r.content,
                                                                                                     "utf-8").lower()


@pytest.mark.django_db
def test_queryset_visibility(api_client, user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    t1 = user_with_profile(username="t1", role="tenant")
    t2 = user_with_profile(username="t2", role="tenant")
    l = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.AVAILABLE)

    # две брони: одна t1, другая t2
    b1 = baker.make("bookings.Booking", listing=l, tenant=t1, start_date=date.today() + timedelta(days=10),
                    end_date=date.today() + timedelta(days=12), status="pending")
    b2 = baker.make("bookings.Booking", listing=l, tenant=t2, start_date=date.today() + timedelta(days=20),
                    end_date=date.today() + timedelta(days=22), status="pending")

    # t1 видит только свою + (если ты разрешаешь) свои по своим объявлениям — здесь только своя
    api_client.force_authenticate(user=t1)
    r_t1 = api_client.get(BASE)
    assert r_t1.status_code == 200
    ids_t1 = {item["id"] for item in r_t1.json()}
    assert ids_t1 == {b1.id}

    # landlord видит обе (по своим объявлениям)
    api_client.force_authenticate(user=landlord)
    r_ll = api_client.get(BASE)
    assert r_ll.status_code == 200
    ids_ll = {item["id"] for item in r_ll.json()}
    assert ids_ll == {b1.id, b2.id}


@pytest.mark.django_db
def test_confirm_and_reject_permissions(api_client, user_with_profile):
    landlord = user_with_profile(username="ll", role="landlord")
    tenant = user_with_profile(username="tt", role="tenant")
    l = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.AVAILABLE)
    b = baker.make("bookings.Booking", listing=l, tenant=tenant, start_date=date.today() + timedelta(days=7),
                   end_date=date.today() + timedelta(days=9), status="pending")

    # tenant не может confirm
    api_client.force_authenticate(user=tenant)
    r_forbidden = api_client.post(f"{BASE}{b.id}/confirm/")
    assert r_forbidden.status_code in (403, 404)

    # landlord может confirm
    api_client.force_authenticate(user=landlord)
    r_ok = api_client.post(f"{BASE}{b.id}/confirm/")
    assert r_ok.status_code == 200
    assert r_ok.json().get("status") == "confirmed"

    # повторный confirm — 400
    r_again = api_client.post(f"{BASE}{b.id}/confirm/")
    assert r_again.status_code == 400

    # reject после confirm — 400 (нельзя переводить из confirmed в rejected)
    r_reject = api_client.post(f"{BASE}{b.id}/reject/")
    assert r_reject.status_code == 400


@pytest.mark.django_db
def test_cancel_with_deadline(api_client, user_with_profile, settings):
    settings.BOOKING_CANCEL_DEADLINE_DAYS = 2
    landlord = user_with_profile(username="ll", role="landlord")
    tenant = user_with_profile(username="tt", role="tenant")
    l = baker.make("listings.Listing", landlord=landlord, status=ListingStatus.AVAILABLE)

    # кейс 1: позволено (старт через 3 дня, дедлайн = 2 дня -> сегодня ещё можно)
    b1 = baker.make("bookings.Booking", listing=l, tenant=tenant, start_date=date.today() + timedelta(days=3),
                    end_date=date.today() + timedelta(days=5), status="pending")
    api_client.force_authenticate(user=tenant)
    r_ok = api_client.post(f"{BASE}{b1.id}/cancel/")
    assert r_ok.status_code == 200
    assert r_ok.json().get("status") == "cancelled"

    # повторная отмена — 400
    r_again = api_client.post(f"{BASE}{b1.id}/cancel/")
    assert r_again.status_code == 400

    # кейс 2: не позволено (старт через 1 день -> «в день заезда или позже» запрещено)
    b2 = baker.make("bookings.Booking", listing=l, tenant=tenant, start_date=date.today() + timedelta(days=1),
                    end_date=date.today() + timedelta(days=2), status="pending")
    r_bad = api_client.post(f"{BASE}{b2.id}/cancel/")
    assert r_bad.status_code == 400
