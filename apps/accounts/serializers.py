from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})  # qo'shildi

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'password_confirm',

        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': _("Password fields didn't match.")
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')  # modelga kerak emas
        user = User.objects.create_user(
            username=validated_data.get('username'),
            password=validated_data.get('password'),
        )
        return user



class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            if not user:
                raise serializers.ValidationError(
                    _("Unable to log in with provided credentials. "),
                    code='authorization'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    _('User account is disabled. ')
                )
            attrs['user'] = user
            return attrs
        raise serializers.ValidationError(
            _("Must include 'username' and 'password'. "),
            code='authorization'
        )


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'phone', 'address', 'date_of_birth',
            'is_staff', 'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'username', 'email', 'is_staff',
            'date_joined', 'last_login'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone',
            'address', 'date_of_birth'
        ]


class ChangePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={
            'input_type': 'password'
        }
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={
            'input_type': 'password'
        }
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={
            'input_type': 'password'
        }
    )

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': _("Password fields didn't match. ")
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_("Old password is incorrect."))
        return value

class UserListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name',
            'is_staff', 'is_active', 'date_joined'
        ]
        read_only_fields = fields