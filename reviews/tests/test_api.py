import pytest
from datetime import date, timedelta
from model_bakery import baker

BASE = "/api/reviews/"


@pytest.mark.django_db
def test_create_review_success(api_client, user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")

    # подтверждённая и завершившаяся бронь
    b = baker.make("bookings.Booking", listing=listing, tenant=tt,
                   start_date=date.today() - timedelta(days=5),
                   end_date=date.today() - timedelta(days=2),
                   status="confirmed")

    api_client.force_authenticate(user=tt)
    r = api_client.post(BASE, {"booking": b.id, "rating": 4, "comment": "ok"}, format="json")
    assert r.status_code in (201, 200)
    data = r.json()
    assert data["rating"] == 4
    # listing подставился, tenant_info присутствует
    assert data["tenant_info"]["username"] == "tt"
    assert data["id"] > 0


@pytest.mark.django_db
def test_create_review_unauth_forbidden(api_client, user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    b = baker.make("bookings.Booking", listing=listing, tenant=tt,
                   start_date=date.today() - timedelta(days=5),
                   end_date=date.today() - timedelta(days=2),
                   status="confirmed")

    r = api_client.post(BASE, {"booking": b.id, "rating": 5}, format="json")
    assert r.status_code in (401, 403)


@pytest.mark.django_db
def test_create_review_duplicate_rejected(api_client, user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    b = baker.make("bookings.Booking", listing=listing, tenant=tt,
                   start_date=date.today() - timedelta(days=5),
                   end_date=date.today() - timedelta(days=2),
                   status="confirmed")

    api_client.force_authenticate(user=tt)
    r1 = api_client.post(BASE, {"booking": b.id, "rating": 5}, format="json")
    assert r1.status_code in (201, 200)

    r2 = api_client.post(BASE, {"booking": b.id, "rating": 4}, format="json")
    assert r2.status_code == 400  # «По этой брони отзыв уже оставлен»


@pytest.mark.django_db
def test_update_delete_permissions(api_client, user_with_profile):
    ll = user_with_profile(username="ll", role="landlord")
    tt = user_with_profile(username="tt", role="tenant")
    other = user_with_profile(username="oth", role="tenant")
    listing = baker.make("listings.Listing", landlord=ll, status="available")
    b = baker.make("bookings.Booking", listing=listing, tenant=tt,
                   start_date=date.today() - timedelta(days=5),
                   end_date=date.today() - timedelta(days=2),
                   status="confirmed")

    # создаёт владелец отзыва
    api_client.force_authenticate(user=tt)
    r = api_client.post(BASE, {"booking": b.id, "rating": 3, "comment": "meh"}, format="json")
    assert r.status_code in (201, 200)
    review_id = r.json()["id"]
    detail = f"{BASE}{review_id}/"

    # другой пользователь — 403 на изменение/удаление
    api_client.force_authenticate(user=other)
    r_forbid = api_client.patch(detail, {"rating": 2}, format="json")
    assert r_forbid.status_code == 403
    d_forbid = api_client.delete(detail)
    assert d_forbid.status_code == 403

    # владелец может обновить и удалить
    api_client.force_authenticate(user=tt)
    r_ok = api_client.patch(detail, {"rating": 5}, format="json")
    assert r_ok.status_code in (200, 202)
    d_ok = api_client.delete(detail)
    assert d_ok.status_code in (200, 202, 204)
