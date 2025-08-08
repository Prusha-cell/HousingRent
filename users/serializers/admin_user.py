from django.contrib.auth.models import User
from rest_framework import serializers
from users.models import UserProfile
from users.choices import UserRole


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role',)


class AdminUserWriteSerializer(serializers.ModelSerializer):
    # делаем вложенный профайл записываемым
    profile = UserProfileSerializer()
    # пароль принимаем в чистом виде, но не возвращаем наружу
    password = serializers.CharField(write_only=True, min_length=8, required=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'password', 'is_active', 'is_staff', 'profile'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        # отделяем вложенные данные профиля
        profile_data = validated_data.pop('profile', {}) or {}
        raw_password = validated_data.pop('password')

        # создаём пользователя + хешируем пароль
        user = User(**validated_data)
        user.set_password(raw_password)
        user.save()

        # создаём/обновляем профиль с ролью (защита от дублей, если есть сигнал post_save)
        role = profile_data.get('role', UserRole.TENANT)
        UserProfile.objects.update_or_create(user=user, defaults={'role': role})

        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        raw_password = validated_data.pop('password', None)

        # обновляем обычные поля
        for k, v in validated_data.items():
            setattr(instance, k, v)

        if raw_password:
            instance.set_password(raw_password)
        instance.save()

        # при апдейте позволяем менять роль
        if profile_data is not None:
            role = profile_data.get('role')
            if role:
                instance.profile.role = role
                instance.profile.save()

        return instance

    def to_representation(self, instance):
        """Вернём роль в привычном виде."""
        data = super().to_representation(instance)
        data['profile'] = {'role': instance.profile.role}
        return data
