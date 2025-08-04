from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet


router = DefaultRouter()
router.register(r'', BookingViewSet)

urlpatterns = [
    path('', include(router.urls)),   # означает «возьми все сгенерированные router-ом пути и прикрути их здесь,
]                                     # на текущий базовый URL модуля»
