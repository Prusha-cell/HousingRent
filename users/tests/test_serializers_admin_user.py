import pytest
from django.contrib.auth.models import User
from users.serializers.admin_user import AdminUserWriteSerializer


@pytest.mark.django_db
def test_admin_user_create_with_profile_role():
    data = {
        "username": "newbie",
        "email": "newbie@example.com",
        "first_name": "New",
        "last_name": " Bee",
        "password": "strongpass123",
        "is_active": True,
        "is_staff": False,
        "profile": {"role": "landlord"},
    }
    ser = AdminUserWriteSerializer(data=data)
    assert ser.is_valid(), ser.errors
    user = ser.save()

    assert isinstance(user, User)
    assert user.check_password("strongpass123")
    assert user.profile.role == "landlord"


@pytest.mark.django_db
def test_admin_user_update_password_and_role(user_with_profile):
    user = user_with_profile(username="editme", password="oldpass123", role="tenant")
    ser = AdminUserWriteSerializer(instance=user, data={
        "username": "editme",
        "email": "e@e.com",
        "first_name": "",
        "last_name": "",
        "is_active": True,
        "is_staff": False,
        "password": "newpass123",  # write_only
        "profile": {"role": "admin"},  # апдейтим роль
    }, partial=True)
    assert ser.is_valid(), ser.errors
    user = ser.save()

    assert user.check_password("newpass123")
    assert user.profile.role == "admin"
