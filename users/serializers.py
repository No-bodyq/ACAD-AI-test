from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.authtoken.models import Token


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())])
    token = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_staff",
            "is_active",
            "date_joined",
            "token",
            "password",
        ]
        read_only_fields = ["id", "date_joined", "token"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        try:
            Token.objects.get_or_create(user=user)
        except Exception:
            pass
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def get_token(self, obj):
        # return the token key for this user (create if missing)
        try:
            token, _ = Token.objects.get_or_create(user=obj)
            return token.key
        except Exception:
            return None
