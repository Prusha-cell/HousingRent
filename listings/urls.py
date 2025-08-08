from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ListingViewSet, MyListingViewSet

router = DefaultRouter()
router.register(r'listings', ListingViewSet, basename='listings')
router.register(r'my-listings', MyListingViewSet, basename='my-listings')

urlpatterns = [
    path('', include(router.urls)),
]
