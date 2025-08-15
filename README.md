# HousingRent (Django + DRF)

A modular rental platform built with **Django** and **Django REST Framework**.

**Modules**

- **users** – `auth.User` + `UserProfile` with roles: `tenant`, `landlord`, `admin`.
- **listings** – landlords' rental listings (statuses: `available` / `unavailable`, view counter).
- **bookings** – booking flow (statuses: `pending`, `confirmed`, `rejected`, `cancelled`).
- **reviews** – tenant reviews tied to finished bookings (one review per booking).
- **analytics** – search history and listing views (+ signal increments listing view counter).

---

## Quick start

### Requirements
- Python 3.11+ (developed and tested on 3.12/3.13)
- Django 4.x and DRF 3.x (installed from `requirements.txt`)
- Database: **MySQL** (prod) or **SQLite** (local/tests)

### Setup

1) **Create a virtualenv and install deps**
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

2) **Environment variables** (MySQL). Create `.env` in project root:
```
# Django
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Database (MySQL)
DB_NAME=housingrent
DB_USER=housingrent
DB_PASSWORD=yourpass
DB_HOST=127.0.0.1
DB_PORT=3306

# Business settings
BOOKING_CANCEL_DEADLINE_DAYS=1  # how many days before check-in a booking can be cancelled
```

> For quick local runs you may switch to SQLite in your settings (or use `settings_test.py`).

3) **Migrate and create a superuser**
```bash
python manage.py migrate
python manage.py createsuperuser
```

4) **(Optional) Load sample data**
```bash
python manage.py loaddata data_utf8.json
```
> Django reads/writes fixtures in **UTF-8**. Export example:  
> `python manage.py dumpdata --indent 2 > data_utf8.json`

5) **Run the server**
```bash
python manage.py runserver
```
Admin: `http://127.0.0.1:8000/admin/`

---

## Architecture & business rules

### users
- `UserProfile (OneToOne → auth.User)` stores `role` (`tenant` / `landlord` / `admin`) and `is_verified`.
- Business rule: if `is_verified=True`, the profile is forced to **landlord** on save.
- A signal creates the profile when a new user is created.
- Serializers:
  - `AdminUserWriteSerializer` – admin user creation with nested `profile.role` and password hashing.
  - Profile serializers for proxy models `Tenant` / `Landlord` (public read-only info).

### listings
- `Listing` belongs to a landlord (`landlord = ForeignKey(User)`).
- Public list (read-only) and “my listings” (CRUD for the owner).
- `views_count` is incremented by an analytics signal when a `ListingView` is created.

### bookings
- A user **cannot book their own listing**.
- Validations: listing availability, date ranges, no overlaps.
- Cancellation allowed up to `BOOKING_CANCEL_DEADLINE_DAYS` before start date.
- Actions:
  - `POST /api/bookings/<id>/confirm/` — owner only; allowed **only from `pending`** → `confirmed`.
  - `POST /api/bookings/<id>/reject/` — owner only; allowed **only from `pending`** → `rejected`.
  - `POST /api/bookings/<id>/cancel/` — tenant only; before deadline → `cancelled`.
- Visibility:
  - Tenants see **their own** bookings.
  - Landlords see bookings for **their listings**.
  - Admins may see everything.

### reviews
- Only the **tenant** of a **confirmed** and **finished** booking can write a review.
- **One review per booking** (DB uniqueness + serializer checks).
- `listing` is inferred from `booking` automatically.
- Owner/admin can update or delete the review.

### analytics
- `SearchHistory(user, keyword, searched_at)` — free-form search history.
- `ListingView(user, listing, viewed_at)` — listing view events.
- `post_save(ListingView)` signal increments `listing.views_count`.

---

## API (main endpoints)

Base API prefix: `/api/` (may differ in your `config/urls.py`).

### Listings
Public (read-only):
```
GET    /api/listings/listings/
GET    /api/listings/listings/<id>/
```

My listings (landlord):
```
GET    /api/listings/my-listings/
POST   /api/listings/my-listings/
PATCH  /api/listings/my-listings/<id>/
DELETE /api/listings/my-listings/<id>/
```

### Bookings
```
GET    /api/bookings/                         # tenant: own; landlord: for own listings
POST   /api/bookings/                         # create booking (tenant; cannot book own listing)

POST   /api/bookings/<id>/confirm/            # owner only, from pending → confirmed
POST   /api/bookings/<id>/reject/             # owner only, from pending → rejected
POST   /api/bookings/<id>/cancel/             # tenant only, before deadline → cancelled
```

### Reviews
```
GET    /api/reviews/
POST   /api/reviews/                          # tenant of finished confirmed booking
PATCH  /api/reviews/<id>/
DELETE /api/reviews/<id>/
```

### Analytics
```
GET    /api/analytics/search-history/         # current user’s searches
POST   /api/analytics/search-history/         # user is set from request (HiddenField)

GET    /api/analytics/listing-views/          # current user’s views
POST   /api/analytics/listing-views/          # creates a view; signal increments listing.views_count
```

> Auth: for dev, **SessionAuth** (log into admin) is enough. If JWT (simplejwt) is enabled, use `Authorization: Bearer <token>`.

---

## Testing

Powered by `pytest`, `pytest-django`, `model_bakery`, and DRF’s `APIClient`.

Run all tests and coverage:
```bash
pytest
pytest --cov=. --cov-report=term-missing
```

Filter by pattern:
```bash
pytest -k "listings and api" -q
```

### Handy fixtures
- `api_client` — DRF `APIClient`.
- `user_with_profile(username, role, verified=False, **kwargs)` — creates a `User` and a synced `UserProfile`.  
  The fixture refreshes `user.profile` to avoid OneToOne cache mismatches during tests.

---

## Useful commands

Create/update superuser:
```bash
python manage.py createsuperuser
```

Dump / load data:
```bash
python manage.py dumpdata --indent 2 > data_utf8.json
python manage.py loaddata data_utf8.json
```

Reset local DB & migrations (⚠️ destructive):
```bash
# This will remove local data and migration files
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

---

## Project layout (short)
```
config/
  settings.py
  settings_test.py
  urls.py
users/
  models.py                # UserProfile, signals, Tenant/Landlord proxies
  serializers/             # admin_user.py, profiles.py, registration_for_users.py
  views.py, urls.py
listings/
  models.py, views.py (ReadOnly + MyListingViewSet), permissions.py, urls.py
bookings/
  models.py, serializers.py, views.py (confirm/reject/cancel), urls.py, choices.py
reviews/
  models.py, serializers.py, views.py, urls.py, choices.py
analytics/
  models.py, serializers.py, views.py, urls.py, signals.py
tests/
```

---

## FAQ

**Q:** Why does `POST /api/listings/listings/` return `405`?  
**A:** The public viewset is read-only. Create listings via `/api/listings/my-listings/` (landlord role required).

**Q:** Why do I get `404` (not `403`) when patching/deleting someone else’s listing?  
**A:** The “my-listings” queryset is restricted to the current user; for other users the object doesn’t exist → `404`.

**Q:** Why can’t I cancel a booking?  
**A:** Check `BOOKING_CANCEL_DEADLINE_DAYS` and the check-in date — cancellation is blocked on the start day and later.

---


