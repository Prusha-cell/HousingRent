from rest_framework import serializers
from .models import SearchHistory, ListingView


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ('id', 'user', 'keyword', 'searched_at')
        read_only_fields = ('id', 'searched_at')


class ListingViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingView
        fields = ('id', 'user', 'listing', 'viewed_at')
        read_only_fields = ('id', 'viewed_at')
