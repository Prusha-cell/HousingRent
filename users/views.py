from datetime import date

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Prefetch
from rest_framework import viewsets, permissions, mixins, status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from bookings.choices import BookingStatus
from bookings.models import Booking
from listings.choices import ListingStatus
from listings.models import Listing
from .models import Tenant, Landlord
from users.serializers.profiles import (
    TenantSerializer,
    LandlordSerializer,
)
from .serializers.admin_user import AdminUserWriteSerializer
from .serializers.registration_for_users import UserRegisterSerializer


class AdminUserViewSet(viewsets.ModelViewSet):
    # Preload related profile via JOIN so admin can see user+profile in one query
    queryset = User.objects.select_related('profile').all()
    serializer_class = AdminUserWriteSerializer
    permission_classes = [permissions.IsAdminUser]


# Endpoint /api/tenants/ — only users with TENANT role (via proxy model)
class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [IsAdminUser]
    queryset = (
        Tenant.objects.all()
        .prefetch_related(
            Prefetch(
                'bookings',
                queryset=Booking.objects.filter(status=BookingStatus.CONFIRMED,
                                                end_date__gte=date.today())

                .select_related('tenant', 'listing'),
                to_attr='prefetched_current_bookings'
            )
        )
    )


# Endpoint /api/landlords/ — only users with LANDLORD role (via proxy model)
class LandlordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LandlordSerializer
    permission_classes = [IsAdminUser]
    queryset = (
        Landlord.objects.all()
        .prefetch_related(
            Prefetch(
                'listings',
                queryset=Listing.objects.filter(status=ListingStatus.AVAILABLE),
                to_attr='prefetched_active_listings'
            )
        )
    )


class UserRegisterView(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    POST /api/users/register/
    """
    # Dummy queryset so DRF won’t expose list/retrieve by default for this ViewSet
    queryset = User.objects.none()
    serializer_class = UserRegisterSerializer

    # Disable global JWT auth for this endpoint
    authentication_classes = []
    permission_classes = [AllowAny]


def set_jwt_cookies(response, user):
    """
    Generate a token pair for the user and set them as HttpOnly cookies.
    """
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    refresh_token = str(refresh)

    # Adjust cookie security flags per your deployment profile
    response.set_cookie(
        'access_token',
        access,
        httponly=True,
        samesite='Lax',
        # secure=True,  # enable in production over HTTPS
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

    Issues JWT tokens into HttpOnly cookies.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Build the response and attach cookies right away
        response = Response({"detail": "Login successful"}, status=status.HTTP_200_OK)
        set_jwt_cookies(response, user)
        return response


class LogoutView(APIView):
    """
    POST /api/logout/ — removes cookies and blacklists the refresh_token.
    """
    # You may allow anonymous calls here so it’s idempotent
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # 1) Get refresh token from cookies and blacklist it (if configured)
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                # Either Simple JWT blacklist app isn’t enabled or token is invalid
                pass

        # 2) Clear cookies
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
