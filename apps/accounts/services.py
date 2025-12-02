from typing import Dict, Optional
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserService:
    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @staticmethod
    @transaction.atomic
    def create_user(validated_data: dict) -> User:
        from apps.cart.models import Cart

        user = User.objects.create_user(**validated_data)
        Cart.objects.create(user=user)

        return user

    @staticmethod
    def update_user(user: User, validated_data: dict) -> User:

        for attr, value in validated_data.items():
            setattr(user, attr, value)
        user.save(update_fields=validated_data.keys())

        return user

    @staticmethod
    def change_password(user: User, new_password: str) -> None:
        user.set_password(new_password)
        user.save(update_fields=['password'])

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        try:
            return User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def user_exists(email: Optional[str] = None, username: Optional[str] = None) -> bool:
        query = User.objects.all()

        if email:
            query = query.filter(email=email.lower())
        if username:
            query = query.filter(username=username)

        return query.exists()