from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .models import SearchHistory, ListingView
from .serializers import SearchHistorySerializer, ListingViewSerializer


class SearchHistoryViewSet(viewsets.ModelViewSet):
    """
    List:
      Returns the current user's search history.

    Create:
      Adds a new search history entry (keyword comes from the payload).
      The `user` field is set automatically.
    """
    serializer_class = SearchHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only entries for the current user
        return SearchHistory.objects.filter(user=self.request.user)


class ListingViewViewSet(viewsets.ModelViewSet):
    """
    List:
      Returns the current user's listing view events.

    Create:
      Creates a new listing view entry (listing comes from the payload).
      The `user` field is set automatically.
    """
    serializer_class = ListingViewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            ListingView.objects
            .filter(user=self.request.user)
            .select_related("listing")
            .order_by("-viewed_at")
        )

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        obj = ser.save()
        out = self.get_serializer(obj).data
        created = ser.context.get("was_created", True)
        return Response(
            out,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            headers=self.get_success_headers(out) if created else {},
        )
