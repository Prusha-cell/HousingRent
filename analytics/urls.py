from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SearchHistoryViewSet, ListingViewViewSet


router = DefaultRouter()
router.register(r'search-history', SearchHistoryViewSet, basename='search history')
router.register(r'listing-views', ListingViewViewSet, basename='listing view')


urlpatterns = [
    path('', include(router.urls)),
]
