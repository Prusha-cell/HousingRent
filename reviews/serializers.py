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
