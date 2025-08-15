from django.contrib.auth.models import User
from rest_framework import serializers
from users.models import UserProfile
from users.choices import UserRole


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("role",)


class AdminUserWriteSerializer(serializers.ModelSerializer):
    # Make the nested profile writable
    profile = UserProfileSerializer()
    # Accept raw password on input but never return it
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_active",
            "is_staff",
            "profile",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {}) or {}
        raw_password = validated_data.pop("password")

        # 1) Create the user
        user = User.objects.create_user(password=raw_password, **validated_data)

        # 2) Ensure the profile exists (signal may have created it already)
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # 3) If a role was provided, update it directly (without triggering save()/signals)
        role = profile_data.get("role")
        if role:
            UserProfile.objects.filter(pk=profile.pk).update(role=role)

            # Clear the reverse OneToOne cache and refresh from DB
            # so user.profile reflects the updated role immediately.
            try:
                del user.profile
            except AttributeError:
                pass
            user.refresh_from_db()

        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        raw_password = validated_data.pop("password", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        if raw_password:
            instance.set_password(raw_password)
        instance.save()

        if profile_data is not None:
            role = profile_data.get("role")
            if role:
                instance.profile.role = role
                instance.profile.save()

        return instance

    def to_representation(self, instance):
        """Return the role in a simple nested structure."""
        data = super().to_representation(instance)
        data["profile"] = {"role": instance.profile.role}
        return data
