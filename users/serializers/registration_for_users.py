from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,
                                     required=True,
                                     style={'input_type': 'password'},
                                     validators=[validate_password],
                                     )
    password_2 = serializers.CharField(write_only=True,
                                       required=True,
                                       style={'input_type': 'password'},
                                       validators=[validate_password],
                                       )
    email = serializers.EmailField(required=True,
                                   validators=[UniqueValidator(queryset=User.objects.all())],
                                   )
    username = serializers.CharField(required=True,
                                     validators=[UniqueValidator(queryset=User.objects.all())],
                                     )

    class Meta:
        model = User
        fields = ['username', 'password', 'password_2', 'email']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_2']:
            raise serializers.ValidationError({'password': 'password do not match.'})

        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
        )
        return user

