from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            **UserSerializer(user).data,
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'token_type': 'bearer',
        }, status=status.HTTP_201_CREATED)
    
    error_msg = "Registration failed."
    if serializer.errors:
        # Get the first error message from the serializer
        first_field = list(serializer.errors.keys())[0]
        first_error = serializer.errors[first_field][0]
        error_msg = f"{first_field}: {first_error}"
        
    return Response({"detail": error_msg}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        response = Response({
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'token_type': 'bearer',
        }, status=status.HTTP_200_OK)
        # Set httpOnly cookies for frontend compatibility
        response.set_cookie(
            key='access_token',
            value=tokens['access'],
            httponly=True,
            samesite='Lax',
            max_age=30 * 60,
        )
        response.set_cookie(
            key='refresh_token',
            value=tokens['refresh'],
            httponly=True,
            samesite='Lax',
            max_age=7 * 24 * 60 * 60,
        )
        return response
    
    # Format DRF errors to match the frontend's expectation of {"detail": "..."}
    error_msg = "Invalid username or password."
    if "non_field_errors" in serializer.errors:
        error_msg = serializer.errors["non_field_errors"][0]
    return Response({"detail": error_msg}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_users_view(request):
    from .models import CustomUser
    users = CustomUser.objects.all()
    return Response({
        "users": [{"id": str(u.id), "username": u.username, "email": u.email, "role": u.role} for u in users]
    })


from rest_framework_simplejwt.views import TokenRefreshView

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            access_token = response.data.get('access')
            if access_token:
                response.set_cookie(
                    key='access_token',
                    value=access_token,
                    httponly=True,
                    samesite='Lax',
                    max_age=30 * 60,
                )
        return response

