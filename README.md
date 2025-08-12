# HousingRent (Django + DRF)

A clean, modular rental platform built on **Django** and **Django REST Framework**.  
Domain modules:

- **users** — базовый `auth.User` + профиль `UserProfile` с ролями: `tenant`, `landlord`, `admin`.
- **listings** — объявления арендодателей (статусы: `available` / `unavailable`, счётчик просмотров).
- **bookings** — бронирования объявлений (статусы: `pending`, `confirmed`, `rejected`, `cancelled`).
- **reviews** — отзывы арендаторов по завершённым бронированиям (один отзыв на одну бронь).
- **analytics** — история поисковых запросов и просмотров объявлений (+ сигнал инкремента счётчика просмотров).

---

## Quick start

### Requirements
- Python 3.11+ (проект разрабатывался на 3.12/3.13 — подходит)
- Django 4.x / DRF 3.x (устанавливаются из `requirements.txt`)
- БД: **MySQL** (прод) или **SQLite** (локально/тесты)

### Setup

1) **Создайте окружение и поставьте зависимости**
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) **Настройте окружение** (MySQL) — создайте файл `.env` в корне проекта:
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
BOOKING_CANCEL_DEADLINE_DAYS=1  # сколько дней до заезда доступна отмена брони
```

> Для локального старта можно использовать SQLite: выставьте переменные БД как в вашем `settings.py` (или используйте `settings_test.py`).

3) **Прогоните миграции и создайте админа**
```bash
python manage.py migrate
python manage.py createsuperuser
```

4) **(опционально) загрузите пример данных**
```bash
python manage.py loaddata data_utf8.json
```
> Django сериализует/читает фикстуры в **UTF-8**. Для выгрузки можно использовать:  
> `python manage.py dumpdata --indent 2 > data_utf8.json`

5) **Запустите сервер**
```bash
python manage.py runserver
```

Админ-панель: `http://127.0.0.1:8000/admin/`

---

## Архитектура и доменная логика

### users
- `UserProfile (OneToOne → auth.User)` хранит роль (`tenant` / `landlord` / `admin`) и флаг `is_verified`.
- Бизнес-правило: если `is_verified=True`, профиль принудительно переводится в роль **landlord** при сохранении.
- Сигнал создаёт профиль при появлении нового пользователя.
- Сериализаторы:
  - `AdminUserWriteSerializer` — админское создание пользователей с вложенным `profile.role` и установкой пароля.
  - Профильные сериализаторы для прокси-моделей `Tenant` / `Landlord` (чтение публичных данных пользователя).

### listings
- `Listing` принадлежит арендодателю (`landlord = ForeignKey(User)`).
- Публичный список (только чтение) и «мои объявления» для владельца (CRUD).
- `views_count` увеличивается сигналом при создании `ListingView` (из модуля `analytics`).

### bookings
- Нельзя бронировать **собственное** объявление.
- Валидации: доступность объявления, корректность дат, отсутствие пересечений.
- Отмена доступна до дедлайна: `BOOKING_CANCEL_DEADLINE_DAYS` (по умолчанию 1).
- Экшены:
  - `POST /api/bookings/<id>/confirm/` — только владелец объявления, только из `pending` → `confirmed`.
  - `POST /api/bookings/<id>/reject/` — только владелец объявления, только из `pending` → `rejected`.
  - `POST /api/bookings/<id>/cancel/` — только арендатор, до дедлайна, из статусов, допускающих отмену → `cancelled`.
- Видимость:
  - Арендатор видит **свои** брони.
  - Арендодатель видит брони **по своим** объявлениям.
  - Администратор может видеть всё.

### reviews
- Отзыв может оставить **только арендатор** по **своей** броне, которая **подтверждена** и уже **завершилась**.
- **Один отзыв на одну бронь** (уникальность на уровне БД/сериализатора).
- `listing` выводится/связывается автоматически через выбранную `booking`.
- Редактировать/удалять отзыв может владелец или админ.

### analytics
- `SearchHistory(user, keyword, searched_at)` — история поисковых запросов.
- `ListingView(user, listing, viewed_at)` — просмотры объявлений.
- Сигнал `post_save(ListingView)` инкрементит `listing.views_count`.

---

## API (основные эндпоинты)

Базовый префикс API: `/api/` (может отличаться, смотрите `config/urls.py`).

### Listings
Публичный (чтение):
```
GET    /api/listings/listings/                # список публичных объявлений
GET    /api/listings/listings/<id>/           # детально
```

Мои объявления (для landlord):
```
GET    /api/listings/my-listings/             # только мои
POST   /api/listings/my-listings/             # создать (требуется роль landlord)
PATCH  /api/listings/my-listings/<id>/        # редактировать (только владелец)
DELETE /api/listings/my-listings/<id>/        # удалить   (только владелец)
```

### Bookings
```
GET    /api/bookings/                         # мои брони (tenant) / брони по моим объявлениям (landlord)
POST   /api/bookings/                         # создать бронь (tenant; нельзя бронировать своё объявление)

POST   /api/bookings/<id>/confirm/            # только владелец объявления, из pending → confirmed
POST   /api/bookings/<id>/reject/             # только владелец объявления, из pending → rejected
POST   /api/bookings/<id>/cancel/             # только арендатор, до дедлайна → cancelled
```

### Reviews
```
GET    /api/reviews/                          # список отзывов
POST   /api/reviews/                          # создать (только арендатор своей завершённой confirmed-брони)
PATCH  /api/reviews/<id>/                     # изменить (владелец/админ)
DELETE /api/reviews/<id>/                     # удалить  (владелец/админ)
```

### Analytics
```
GET    /api/analytics/search-history/         # мои поисковые запросы
POST   /api/analytics/search-history/         # создать запись (user проставляется автоматически)

GET    /api/analytics/listing-views/          # мои просмотры
POST   /api/analytics/listing-views/          # создать просмотр (инкрементирует listing.views_count сигналом)
```

> Аутентификация: в dev обычно **SessionAuth** (через логин в админке). Если подключён JWT (simplejwt), используйте заголовок `Authorization: Bearer <token>`.

---

## Тестирование

Проект тестируется `pytest` + `pytest-django` + `model_bakery` + `DRF APIClient`.

Запуск всех тестов и покрытие:
```bash
pytest
pytest --cov=. --cov-report=term-missing
```

Запуск части тестов по шаблону:
```bash
pytest -k "listings and api" -q
```

### Полезные фикстуры
- `api_client` — DRF `APIClient`.
- `user_with_profile(username, role, verified=False, **kwargs)` — создаёт `User` и синхронизированный `UserProfile` с нужной ролью.  
  В фикстуре после сохранения профиля сбрасывается кэш `user.profile`, чтобы в тестах не было рассинхронизации OneToOne.

---

## Полезные команды

**Создать/обновить суперпользователя**
```bash
python manage.py createsuperuser
```

**Сделать дамп/загрузку данных**
```bash
python manage.py dumpdata --indent 2 > data_utf8.json
python manage.py loaddata data_utf8.json
```

**Сбросить миграции и базу (локально)**
```bash
# Осторожно: удалит данные!
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

---

## Структура (сокращённо)
```
config/
    settings.py
    settings_test.py
    urls.py
users/
    models.py        # UserProfile, сигналы, прокси Tenant/Landlord
    serializers/     # admin_user.py, profiles.py, registration_for_users.py
    views.py, urls.py
listings/
    models.py, views.py (ReadOnly + MyListingViewSet), permissions.py, urls.py
bookings/
    models.py, serializers.py, views.py (confirm/reject/cancel), urls.py, choices.py
reviews/
    models.py, serializers.py, views.py, urls.py, choices.py
analytics/
    models.py, serializers.py, views.py, urls.py, signals.py
tests/               # модульные и интеграционные тесты по приложениям
```

---

## Частые вопросы

**Q:** Почему POST на `/api/listings/listings/` даёт `405`?  
**A:** Публичный ViewSet — только чтение. Создавать нужно через `/api/listings/my-listings/` (требуется роль landlord).

**Q:** Почему PATCH/DELETE чужого объявления дают `404`, а не `403`?  
**A:** В «моих» объявлениях queryset ограничен текущим пользователем; объект «не существует» для чужого владельца → `404` (так безопаснее).

**Q:** Отмена брони не проходит — почему?  
**A:** Проверьте `BOOKING_CANCEL_DEADLINE_DAYS` и дату заезда: отмена запрещена в день заезда и позже.

---


