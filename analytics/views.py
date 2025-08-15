from rest_framework import viewsets, permissions
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
        # Only entries for the current user
        return ListingView.objects.filter(user=self.request.user)
