from django.utils import timezone
from rest_framework import serializers

from .models import Review
from bookings.models import Booking
from bookings.choices import BookingStatus
from django.contrib.auth import get_user_model

User = get_user_model()


class UserShortSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class ReviewSerializer(serializers.ModelSerializer):
    # кто пишет отзыв — ставим из request.user
    tenant = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tenant_info = UserShortSerializers(source='tenant', read_only=True)

    # клиент присылает только booking; listing выставим автоматически
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    listing = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'booking', 'listing', 'tenant_info', 'tenant', 'rating', 'comment', 'created_at')
        read_only_fields = ('id', 'tenant', 'listing', 'created_at')
        extra_kwargs = {
            # опционально, чтобы не светить в ответе — но на создание он нужен
            'booking': {'write_only': True}
        }

    def validate(self, attrs):
        user = self.context['request'].user
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("Требуется аутентификация.")

        booking = attrs.get('booking') or getattr(self.instance, 'booking', None)
        if booking is None:
            raise serializers.ValidationError({"booking": "Обязательное поле."})

        # Нельзя оставлять отзыв на своё объявление
        if booking.listing.landlord_id == user.id:
            raise serializers.ValidationError("Нельзя оставлять отзыв на собственное объявление.")

        # Бронь должна принадлежать текущему пользователю
        if booking.tenant_id != user.id:
            raise serializers.ValidationError("Отзыв можно оставить только по своей брони.")

        # Бронь — подтверждена и уже завершилась
        today = timezone.localdate()
        if booking.status != BookingStatus.CONFIRMED:
            raise serializers.ValidationError("Отзыв доступен только по подтверждённой брони.")
        if booking.end_date > today:
            raise serializers.ValidationError("Отзыв можно оставить после окончания проживания.")

        # Нельзя второй отзыв по той же брони
        qs = Review.objects.filter(tenant_id=user.id, booking_id=booking.id)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("По этой брони отзыв уже оставлен.")

        # Зафиксировать listing из booking и запретить подмену
        attrs['listing'] = booking.listing

        # На апдейте запрещаем менять бронь
        if self.instance and booking.id != self.instance.booking_id:
            raise serializers.ValidationError("Нельзя менять бронь у существующего отзыва.")

        return attrs
