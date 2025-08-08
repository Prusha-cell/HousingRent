from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Tenant, Landlord
from users.serializers.profiles import (
    TenantSerializer,
    LandlordSerializer,
)
from .serializers.admi_user import AdminUserWriteSerializer
from .serializers.registration_for_users import UserRegisterSerializer


class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('profile').all()  # select_related('profile') выполняет SQL-JOIN,
    serializer_class = AdminUserWriteSerializer  # чтоб сразу отобразить все профили
    permission_classes = [permissions.IsAdminUser]


# Эндпоинт /api/tenants/ (работаем только с теми, у кого роль TENANT)
class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAdminUser]


# Эндпоинт /api/landlords/ (только для роли LANDLORD)
class LandlordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Landlord.objects.all()
    serializer_class = LandlordSerializer
    permission_classes = [IsAdminUser]


class UserRegisterView(mixins.CreateModelMixin,
                       viewsets.GenericViewSet):
    """
    POST /api/users/register/
    """
    queryset = User.objects.none()  # queryset = User.objects.none() — это просто заглушка,
    serializer_class = UserRegisterSerializer  # чтобы DRF-захардкодил пустой набор для всех не-POST действий.

    authentication_classes = []  # <— отключаем глобальные JWTAuth
    permission_classes = [AllowAny]  # разрешаем любому пользователю регистрацию


def set_jwt_cookies(response, user):
    """
    Генерирует пару токенов для user и кладёт в response cookies.
    """
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    refresh_token = str(refresh)

    # Настраиваем флаги безопасности куки по своему профилю
    response.set_cookie(
        'access_token',
        access,
        httponly=True,
        samesite='Lax',
        # secure=True,  # в продакшене по HTTPS
    )
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,
        samesite='Lax',
        # secure=True,
    )


class LoginView(APIView):
    """
    POST /api/login/
    {
      "username": "...",
      "password": "..."
    }
    — выдаёт JWT в HttpOnly-куки.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"detail": "Неверное имя пользователя или пароль."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Собираем ответ и сразу вручаем куки
        response = Response({"detail": "Успешный вход"}, status=status.HTTP_200_OK)
        set_jwt_cookies(response, user)
        return response


class LogoutView(APIView):
    """
    POST /api/logout/ — удаляет куки и заносит refresh_token в blacklist.
    """
    permission_classes = []  # можно разрешить и анонимам

    def post(self, request, *args, **kwargs):
        # 1) Получаем refresh из куки
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                # либо Simple JWT не настроен на blacklist, либо токен некорректен
                pass

        # 2) Удаляем куки
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
