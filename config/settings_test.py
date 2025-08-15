from .settings import *


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "test_db.sqlite3",
    }
}


PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
AUTH_PASSWORD_VALIDATORS = []


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

DEBUG = True
