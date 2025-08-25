from rest_framework import serializers
from django.utils import timezone
from django.db import IntegrityError, transaction
from .models import ListingView, SearchHistory


class SearchHistorySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SearchHistory
        fields = ('id', 'user', 'keyword', 'searched_at')
        read_only_fields = ('id', 'searched_at')


class ListingViewSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ListingView
        fields = ("id", "user", "listing", "viewed_at", "viewed_on")
        read_only_fields = ("id", "viewed_at", "viewed_on", "user")
        validators = []

    def create(self, validated_data):
        user = validated_data["user"]
        listing = validated_data["listing"]
        today = timezone.localdate()

        # idempotent в рамках дня: get_or_create + защита от гонок
        try:
            with transaction.atomic():
                obj, created = ListingView.objects.get_or_create(
                    user=user,
                    listing=listing,
                    viewed_on=today,
                    defaults={"viewed_at": timezone.now()},
                )
        except IntegrityError:
            # если две гонки одновременно создали — берём существующую
            obj = ListingView.objects.get(user=user, listing=listing, viewed_on=today)
            created = False

        if not created:
            obj.viewed_at = timezone.now()
            obj.save(update_fields=["viewed_at"])

        # передадим флаг наружу, чтобы ViewSet мог вернуть 200 вместо 201
        self.context["was_created"] = created
        return obj
