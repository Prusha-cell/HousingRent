import pytest
from django.contrib.auth.models import User
from users.models import UserProfile


@pytest.mark.django_db
def test_verified_user_becomes_landlord():
    u = User.objects.create_user(username="john", password="x")
    # безопасно получаем профиль (если сигнал его создал) или создаём
    profile, _ = UserProfile.objects.get_or_create(user=u, defaults={"role": "tenant"})
    profile.is_verified = True
    profile.save()
    assert profile.role == "landlord"
