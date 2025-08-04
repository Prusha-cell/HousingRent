from rest_framework import viewsets, permissions
from .models import SearchHistory, ListingView
from .serializers import SearchHistorySerializer, ListingViewSerializer


class SearchHistoryViewSet(viewsets.ModelViewSet):
    """
    List:
    Возвращает историю поисковых запросов текущего пользователя.

    Create:
    Добавляет новую запись в историю поиска (keyword берётся из payload).
    Поле user заполняется автоматически.
    """
    serializer_class = SearchHistorySerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только записи текущего пользователя
        return SearchHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Привязываем запись к текущему пользователю
        serializer.save(user=self.request.user)


class ListingViewViewSet(viewsets.ModelViewSet):
    """
    List:
    Возвращает список просмотров объявлений текущего пользователя.

    Create:
    Добавляет запись о просмотре объявления (listing берётся из payload).
    Поле user заполняется автоматически.
    """
    serializer_class = ListingViewSerializer
    # permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ListingView.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
