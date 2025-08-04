from django.contrib.auth.models import User
from .models import UserProfile, Tenant, Landlord
from bookings.serializers import BookingSerializer
from listings.serializers import ListingSerializer
from rest_framework import serializers


class UserProfileSerializer(serializers.ModelSerializer):
    # hidden-поле, автоматически берёт request.user
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = UserProfile
        fields = ('role', 'user')
        read_only_fields = ('user',)   # ('user',) - прописываем как кортеж, так как это итерируемый объект


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)   # read_only=True у вложенного поля защищает его от
                                                      # непреднамеренного изменения через этот сериализатор
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'profile',
        )


# TenantSerializer даёт более явную и ограниченную модель данных для конкретного кейса
class TenantSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)  # source= - источник, от куда
    email = serializers.EmailField(source='user.email', read_only=True)       # берем данные
    current_bookings = serializers.SerializerMethodField()       # SerializerMethodField() - позволяет сериализировать
                                                                 # методы хронящиеся в моделях
    class Meta:
        model = Tenant
        fields = ('id', 'username', 'email', 'current_bookings')

    def get_current_bookings(self, obj):
        # obj — это Tenant instance
        qs = obj.get_current_bookings()
        return BookingSerializer(qs, many=True).data


class LandlordSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    active_listings = serializers.SerializerMethodField(method_name='get_listings')

    class Meta:
        model = Landlord
        fields = (
            'id',
            'username',
            'email',
            'active_listings',
        )

    def get_listings(self, obj):
        # obj — это Landlord instance
        qs = obj.get_listings()
        return ListingSerializer(qs, many=True).data
