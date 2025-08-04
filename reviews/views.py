from rest_framework import permissions, viewsets

from reviews.models import Review
from reviews.serializers import ReviewSerializer


# class IsOwnerOrReadOnly(permissions.BasePermission):
#     def has_object_permission(self, request, view, obj):
#         # всегда можно читать
#         if request.method in permissions.SAFE_METHODS:
#             return True
#         # писать/удалять — только если владелец
#         return obj.tenant == request.user


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    # permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        # возвращаем все отзывы
        return Review.objects.all()
