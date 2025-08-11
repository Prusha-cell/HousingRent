from rest_framework import viewsets, permissions

from reviews.models import Review
from reviews.serializers import ReviewSerializer
from utils.permissions import IsReviewOwnerOrAdmin


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    queryset = Review.objects.select_related('listing', 'tenant', 'booking').all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsReviewOwnerOrAdmin]


