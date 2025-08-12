# conftest.py
import pytest
from django.contrib.auth.models import User
from users.models import UserProfile
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_with_profile():
    def _make(
            username="u", password="password123",
            role="tenant", is_staff=False, is_superuser=False,
            verified=False, **kwargs
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **kwargs
        )
        # гарантируем профиль (сигнал мог уже создать с ролью tenant)
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # ставим нужную роль
        profile.role = role
        # при verified=True твоя модель при save() поднимет роль до landlord
        if verified:
            profile.is_verified = True

        # Сохраняем и СБРАСЫВАЕМ кэш O2O, чтобы user.profile был актуален
        profile.save()
        try:
            del user.profile  # сбить кэш обратной OneToOne
        except AttributeError:
            pass
        user.refresh_from_db()

        return user

    return _make
