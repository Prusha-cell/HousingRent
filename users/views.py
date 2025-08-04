from django.contrib.auth.models import User
from rest_framework import viewsets, permissions

from .models import Tenant, Landlord, UserProfile
from .serializers import (
    UserSerializer,
    TenantSerializer,
    LandlordSerializer,
    UserProfileSerializer,
)


# users/views.py
from rest_framework import generics, permissions
from .models import UserProfile
# from .serializers import UserProfileSerializer

class UserProfileDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    GET /api/users/profile/    — посмотреть
    PATCH /api/users/profile/  — обновить поля (role и т.п.)
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # возвращаем профиль именно того, кто запросил
        return self.request.user.profile



# # Общий ViewSet для работы с профилями (только для админов, например)
# class UserProfileViewSet(viewsets.ModelViewSet):
#     queryset = UserProfile.objects.select_related('user').all()    # select_related('user') выполняет SQL-JOIN,
#     serializer_class = UserProfileSerializer                       # чтобы при выборке UserProfile сразу загрузить
#     # permission_classes = [permissions.IsAdminUser]               #  связанные объекты User одним запросом.


# Эндпоинт /api/users/    (только чтение, например)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSerializer
    # permission_classes = [permissions.IsAuthenticated]


# Эндпоинт /api/tenants/  (работаем только с теми, у кого роль TENANT)
class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    # permission_classes = [permissions.IsAuthenticated]


# Эндпоинт /api/landlords/ (только для роли LANDLORD)
class LandlordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Landlord.objects.all()
    serializer_class = LandlordSerializer
    # permission_classes = [permissions.IsAuthenticated]
