from rest_framework import permissions
from users.choices import UserRole


class IsLandlordOrReadOnly(permissions.BasePermission):
    """
    SAFE_METHODS (GET, HEAD, OPTIONS) — всем разрешено,
    POST/PUT/PATCH/DELETE — только суперюзерам или владельцам-арендодателям.
    """

    def _is_safe_or_superuser(self, request):
        # Разрешаем чтение и админам любые операции
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        return False

    def has_permission(self, request, view):
        # 1) Если это чтение, сразу разрешаем
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2) Для записи пользователь должен быть аутентифицирован
        if not request.user.is_authenticated:
            return False

        # 3) Админ (superuser) может всё
        if request.user.is_superuser:
            return True

        # 4) В противном случае — только арендодатель
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role == UserRole.LANDLORD)

    def has_object_permission(self, request, view, obj):
        # 1) Чтение и админы — всегда разрешено
        if self._is_safe_or_superuser(request):
            return True

        # 2) Для записи — только если это объявление этого же арендодателя
        return obj.landlord_id == request.user.pk


class IsLandlordOwnerOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role == UserRole.LANDLORD)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.landlord_id == request.user.pk


class IsBookingActorOrAdmin(permissions.BasePermission):
    """
    Доступ к объекту брони:
    - админ: всё
    - тот, кто забронировал (tenant)
    - арендодатель этого listing (listing.landlord)
    """

    def has_permission(self, request, view):
        # Любой залогиненный может работать с эндпоинтом (в т.ч. создавать)
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        u = request.user
        if u.is_staff or u.is_superuser:
            return True
        if getattr(obj, "tenant_id", None) == u.pk:
            return True
        if getattr(obj, "listing", None) and getattr(obj.listing, "landlord_id", None) == u.pk:
            return True
        return False


class IsReviewOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.tenant_id == request.user.id
