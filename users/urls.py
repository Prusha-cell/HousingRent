from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet,
    LandlordViewSet, AdminUserViewSet,
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'landlords', LandlordViewSet, basename='landlord')
router.register(r'admin', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    path('', include(router.urls)),
]
