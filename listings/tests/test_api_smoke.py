import pytest


@pytest.mark.django_db
def test_listings_endpoint_is_reachable(api_client):
    # путь подключён как path('api/listings/', include('listings.urls'))
    resp = api_client.get("/api/listings/")
    assert resp.status_code in (200, 301, 302)  # 200 — ок; редирект допустим на стартовом роуте
