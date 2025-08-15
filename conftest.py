import pytest
from django.contrib.auth.models import User
from users.models import UserProfile
from rest_framework.test import APIClient


@pytest.fixture
def as_list():
    """
    Converts a DRF response to a list of items.
Supports both paginated vocabulary and pure list.
    """
    def _as_list(resp):
        data = resp.json()
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        raise AssertionError(f"Unexpected response shape: {type(data)} -> {data}")
    return _as_list


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_with_profile():
    def _make(
        username="u",
        password="password123",
        role="tenant",
        is_staff=False,
        is_superuser=False,
        verified=False,
        **kwargs,
    ):
        user = User.objects.create_user(
            username=username,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
            **kwargs,
        )

        # Ensure a profile exists (the signal may already have created it with the default tenant role)
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # Set the requested role
        profile.role = role

        # If verified=True, your model's save() will promote the role to landlord
        if verified:
            profile.is_verified = True

        # Save and CLEAR the O2O cache so user.profile is up to date
        profile.save()
        try:
            del user.profile  # clear reverse OneToOne cache
        except AttributeError:
            pass
        user.refresh_from_db()

        return user

    return _make
