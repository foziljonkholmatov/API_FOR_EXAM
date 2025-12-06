from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.contrib.auth import get_user_model

from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserListSerializer,
)
from .services import UserService
from .permissions import IsAdminUser

User = get_user_model()


@extend_schema(
    tags=['Auth'],
    summary='User Registration',
    description='Register a new user with username and password',
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiExample(
            'Success',
            value={
                'user': {
                    'id': 1,
                    'username': 'testuser',
                    'email': '',
                    'full_name': '',
                    'is_staff': False,
                    'date_joined': '2025-01-15T10:00:00Z'
                },
                'tokens': {
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                }
            }
        ),
        400: OpenApiExample(
            'Error',
            value={
                'username': ['This field is required.'],
                'password': ['This password is too short.']
            }
        )
    },
    examples=[
        OpenApiExample(
            'Register Request',
            value={
                'username': 'testuser',
                'password': 'SecurePass123!',
                'password_confirm': 'SecurePass123!'
            },
            request_only=True
        )
    ]
)
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_data = serializer.validated_data.copy()
        user_data.pop('password_confirm')

        user = UserService.create_user(user_data)
        tokens = UserService.generate_tokens(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Auth'],
    summary='User Login',
    description='Login with username and password to get JWT tokens',
    request=UserLoginSerializer,
    responses={
        200: OpenApiExample(
            'Success',
            value={
                'user': {
                    'id': 1,
                    'username': 'testuser',
                    'full_name': 'Test User',
                    'is_staff': False
                },
                'tokens': {
                    'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                    'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                }
            }
        ),
        401: OpenApiExample(
            'Error',
            value={
                'error': 'Unable to log in with provided credentials.'
            }
        )
    },
    examples=[
        OpenApiExample(
            'Login Request',
            value={
                'username': 'testuser',
                'password': 'SecurePass123!'
            },
            request_only=True
        )
    ]
)
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        # Generate tokens
        tokens = UserService.generate_tokens(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Auth'],
    summary='User Logout',
    description='Logout user and blacklist refresh token',
    responses={200: {'message': 'Successfully logged out'}}
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            from rest_framework_simplejwt.tokens import RefreshToken

            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()

            return Response({
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['User Profile'],
    summary='Get/Update User Profile',
    description='Get current user profile or update profile information',
    responses={200: UserProfileSerializer}
)
class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserProfileSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_user = UserService.update_user(instance, serializer.validated_data)

        return Response(UserProfileSerializer(updated_user).data)


@extend_schema(
    tags=['User Profile'],
    summary='Change Password',
    description='Change user password',
    request=ChangePasswordSerializer,
    responses={200: {'message': 'Password changed successfully'}}
)
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        UserService.change_password(
            request.user,
            serializer.validated_data['new_password']
        )

        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Admin - Users'],
    summary='List All Users',
    description='Get list of all users (Admin only)',
    responses={200: UserListSerializer(many=True)}
)
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        queryset = super().get_queryset()

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        is_staff = self.request.query_params.get('is_staff')
        if is_staff is not None:
            queryset = queryset.filter(is_staff=is_staff.lower() == 'true')

        return queryset


@extend_schema(
    tags=['Admin - Users'],
    summary='Get User Details',
    description='Get specific user details (Admin only)',
    responses={200: UserProfileSerializer}
)
class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]