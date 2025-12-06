from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

from .serializers import (
    UserListSerializer,
    UserLoginSerializer,
    UserUpdateSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
)
from .services import  UserService
from .permissions import IsAdminUser

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    request=UserRegistrationSerializer,
    responses={201: UserProfileSerializer}
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
    tags=['Authentication'],
    request=UserLoginSerializer,
    responses={200: UserProfileSerializer}
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

        tokens = UserService.generate_tokens(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Authentication'],
    responses={200: None}
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({
                'message': 'Successfully logged out.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'Error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['User Profile'],
    responses={200: UserProfileSerializer}
)
class ProfileView(generics.RetrieveUpdateDestroyAPIView):
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
    responses={200: {'message': 'Password changed successfully '}}
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
    responses={200: UserListSerializer(many=True)}
)
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAdminUser]

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
    tags=['Admin  - Users'],
    responses={200: UserProfileSerializer}
)
class UserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
