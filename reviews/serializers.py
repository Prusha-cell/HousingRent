from django.utils import timezone
from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    tenant = serializers.HiddenField(                   # HiddenField - его задача скрыто подставить в validated_data
        default=serializers.CurrentUserDefault()        # нечто, что не передаёт клиент
    )                                                   # CurrentUserDefault() — это класс-“заглушка” (callable),

                                                        # который при валидации сериализатора берёт из контекста
    class Meta:                                         # самого сериализатора объект request.user.
        model = Review
        fields = ('id', 'listing', 'tenant', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        user = self.context['request'].user
        listing = attrs.get('listing') or getattr(self.instance, 'listing', None)
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Требуется аутентификация.")

        # нельзя ревьювить своё объявление
        if listing and listing.landlord_id == user.id:
            raise serializers.ValidationError("Нельзя оставлять отзыв на собственное объявление.")

        # проверяем наличие брони этого listing у пользователя
        from bookings.models import Booking
        from bookings.choices import BookingStatus
        today = timezone.now().date()
        has_booking = Booking.objects.filter(
            listing=listing,
            tenant=user,
            status__in=[BookingStatus.CONFIRMED],  # добавь сюда статусы, которые для тебя «засчитываются»
            end_date__lte=today
        ).exists()
        if not has_booking:
            raise serializers.ValidationError("Отзыв можно оставить только после своей брони этого объявления.")
        return attrs
