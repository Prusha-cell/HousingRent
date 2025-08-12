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
        profile_data = validated_data.pop("profile", {}) or {}
        raw_password = validated_data.pop("password")

        # 1) создаём пользователя
        user = User.objects.create_user(password=raw_password, **validated_data)

        # 2) гарантируем, что профиль есть (сигнал мог уже создать)
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # 3) если роль передали — обновим напрямую (без сигналов/ save())
        role = profile_data.get("role")
        if role:
            UserProfile.objects.filter(pk=profile.pk).update(role=role)

            # Сбросить кэш связанного объекта и перечитать из БД,
            # чтобы user.profile отдавал уже обновлённую роль.
            try:
                del user.profile  # удаляем кэш обратной OneToOne-ссылки
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
        """Вернём роль в привычном виде."""
        data = super().to_representation(instance)
        data['profile'] = {'role': instance.profile.role}
        return data
