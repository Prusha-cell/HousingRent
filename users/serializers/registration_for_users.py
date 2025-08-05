from users.choices import UserRole
from users.models import UserProfile
from users.serializers.base_registration import BaseUserRegisterSerializer


class GuestRegistrationSerializer(BaseUserRegisterSerializer):
    def create(self, validated_data):
        validated_data.pop('password_2', None)
        user = super().create(validated_data)

        # убираем ручное создание профиля,
        # signal post_save сам создаст UserProfile
        # UserProfile.objects.create(user=user, role=UserRole.GUEST)
        return user
