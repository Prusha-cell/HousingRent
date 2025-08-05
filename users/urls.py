from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    TenantViewSet,
    LandlordViewSet,
    UserProfileDetailAPIView,
    GuestRegisterView)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'landlords', LandlordViewSet, basename='landlord')
router.register(r'guest-register', GuestRegisterView, basename='guest_register')
# router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', UserProfileDetailAPIView.as_view(), name='user-profile-detail'),
]
