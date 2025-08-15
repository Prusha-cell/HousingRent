from rest_framework import permissions
from users.choices import UserRole


class IsLandlordOrReadOnly(permissions.BasePermission):
    """
    SAFE_METHODS (GET, HEAD, OPTIONS) — allowed to everyone.
    POST/PUT/PATCH/DELETE — only for superusers or users with the landlord role.
    Object-level writes are allowed only for the owner (listing.landlord).
    """

    def _is_safe_or_superuser(self, request):
        # Allow read-only and let superusers do anything
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        return False

    def has_permission(self, request, view):
        # 1) Allow all safe (read-only) requests
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2) For write operations the user must be authenticated
        if not request.user.is_authenticated:
            return False

        # 3) Superuser can do everything
        if request.user.is_superuser:
            return True

        # 4) Otherwise only a landlord can write
        profile = getattr(request.user, 'profile', None)
        return bool(profile and profile.role == UserRole.LANDLORD)

    def has_object_permission(self, request, view, obj):
        # 1) Read-only and superusers — always allowed
        if self._is_safe_or_superuser(request):
            return True

        # 2) For writes — only if the object belongs to the same landlord
        return obj.landlord_id == request.user.pk


class IsLandlordOwnerOnly(permissions.BasePermission):
    """
    For the “my listings” endpoints:
    - User must be authenticated.
    - Superusers are allowed to access everything.
    - Otherwise only landlords can access.
    - Object-level access is limited to the owner (listing.landlord).
    """
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
    Access to a booking object is allowed for:
    - Admins/staff
    - The tenant who made the booking
    - The landlord of the related listing (booking.listing.landlord)
    """

    def has_permission(self, request, view):
        # Any authenticated user may access the endpoint (including create)
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
    """
    Reviews:
    - SAFE_METHODS are allowed to everyone.
    - Writes require authentication.
    - Object-level writes allowed to admins or the review owner (tenant).
    """
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
