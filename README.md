# HousingRent

Back-end приложение для аренды жилья на Django + MySQL.

## Структура проекта

Ниже представлена базовая структура директорий и файлов проекта. По ней можно ориентироваться при дальнейшей разработке и расширении функционала.

```text
HousingRent/                # корень проекта
├── config/                  # конфигурация Django
│   ├── __init__.py
│   ├── settings.py          # настройки проекта (env, БД, JWT и т.д.)
│   ├── urls.py              # маршрутизация корневых URL
│   ├── wsgi.py
│   └── asgi.py
│
├── users/                   # приложение users: профили, аутентификация
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # модель UserProfile + прокси-модели
│   ├── choices.py           # перечисления (UserRole и др.)
│   ├── serializers.py       # DRF-сериализаторы
│   ├── views.py             # ViewSets / APIView
│   ├── urls.py              # маршруты users/
│   ├── signals.py           # создание профиля при регистрации
│   └── tests.py             # тесты для users
│
├── listings/                # приложение для объявлений 
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # Listing модель
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── filters.py           # django-filter фильтры (цена, комнаты и т.д.)
│   └── tests.py             # юнит-тесты для объявлений
│
├── bookings/                # приложение бронирований
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # Booking модель
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py             # тесты для бронирований
│
├── reviews/                 # отзывы и рейтинги
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # Review модель
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py             # тесты для отзывов
│
├── analytics/               # история поиска, просмотры, популярность
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py            # SearchHistory, AdView модели
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py             # тесты для аналитики
│
├── manage.py                # точка запуска команд Django
├── .gitignore               # исключения для Git
├── db.sqlite3               # локальная БД для разработки
├── requirements.txt         # зависимости проекта (указывайте версии для воспроизводимости)
├── Dockerfile               # контейнеризация приложения
├── docker-compose.yml       # сервисы (MySQL, Redis, Django)
├── .env                     # приватные настройки окружения
├── staticfiles/             # собранные статические файлы (при использовании WhiteNoise)
└── media/                   # загружаемые медиа-файлы
```

## Описание директорий и файлов

- **config/** — основные настройки Django: окружение, базы данных, CORS, JWT, Celery и т.д.
- **users/** — всё про пользователей: профиль, роли, регистрация, аутентификация, прокси-модели.
- **listings/** — управление объявлениями: модели, API, фильтры.
- **bookings/** — логика бронирования: запросы, подтверждения, отмены.
- **reviews/** — отзывы и рейтинги пользователей, оставленные после бронирования.
- **analytics/** — сбор и отображение статистики: история поисков, просмотры и популярные объявления.
- **manage.py** — точка входа для команд Django.
- **.gitignore** — файлы и папки, игнорируемые Git.
- **db.sqlite3** — локальная база данных для разработки.
- **requirements.txt** — зависимости проекта с указанием версий.
- **Dockerfile**, **docker-compose.yml** — контейнеризация и локальная инфраструктура.
- **.env** — приватные переменные окружения (не хранить в репозитории).
- **staticfiles/** и **media/** — директории для статических и медиа-файлов.

---

### Как начать разработку

1. Склонировать репозиторий:
   ```bash
   git clone <repo-url> HousingRent
   cd HousingRent
   ```
2. Создать и активировать виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Настроить `.env` (скопировать `.env.example` и заполнить переменные).
5. Применить миграции:
   ```bash
   python manage.py migrate
   ```
6. Запустить сервер:
   ```bash
   python manage.py runserver
   ```

Теперь приложение доступно по адресу `http://127.0.0.1:8000/`. Более подробная документация по API — в разделе `docs/` (в разработке).

