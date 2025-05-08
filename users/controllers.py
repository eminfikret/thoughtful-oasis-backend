from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserDetailSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)
from .services import UserService


class UserListController(APIView):
    """Controller for listing all users"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    @swagger_auto_schema(
        operation_summary="List all users",
        operation_description="Get a list of all users",
        responses={200: openapi.Response(
            description="List of users",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            )
        )}
    )
    def get(self, request):
        """Get all users"""
        users = self.user_service.get_all_users()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class RegisterController(APIView):
    """Controller for user registration"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Register a new user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password', 'password2', 'email'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'password2': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Register a new user"""
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = self.user_service.register_user(serializer.validated_data)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginController(APIView):
    """Controller for user login"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    @swagger_auto_schema(
        operation_summary="Login a user",
        operation_description="Login a user and receive an authentication token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(
                description="Successful login",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'token': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            401: "Invalid credentials"
        }
    )
    def post(self, request):
        """Login a user"""
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            result = self.user_service.login_user(
                serializer.validated_data['username'],
                serializer.validated_data['password']
            )
            
            if result:
                return Response({
                    'user': UserSerializer(result['user']).data,
                    'token': result['token']
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailController(APIView):
    """Controller for user detail operations"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    @swagger_auto_schema(
        operation_summary="Get user details",
        operation_description="Get details for a specific user",
        responses={
            200: UserDetailSerializer(),
            404: "User not found"
        }
    )
    def get(self, request, user_id):
        """Get a specific user's details"""
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Update user details",
        operation_description="Update details for a specific user",
        request_body=UserDetailSerializer,
        responses={
            200: UserDetailSerializer(),
            400: "Bad request",
            403: "Permission denied",
            404: "User not found"
        }
    )
    def put(self, request, user_id):
        """Update a specific user's details"""
        # Only allow users to update their own details
        if request.user.id != int(user_id):
            raise PermissionDenied("You can only update your own details")
        
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise NotFound("User not found")
        
        serializer = UserDetailSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileController(APIView):
    """Controller for user profile operations"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Get profile for a specific user",
        responses={
            200: UserProfileSerializer(),
            404: "Profile not found"
        }
    )
    def get(self, request, user_id):
        """Get a specific user's profile"""
        profile = self.user_service.get_user_profile(user_id)
        if not profile:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_summary="Update user profile",
        operation_description="Update profile for a specific user",
        request_body=UserProfileUpdateSerializer,
        responses={
            200: UserProfileSerializer(),
            400: "Bad request",
            403: "Permission denied",
            404: "Profile not found"
        }
    )
    def patch(self, request, user_id):
        """Update a specific user's profile"""
        # Only allow users to update their own profile
        if request.user.id != int(user_id):
            raise PermissionDenied("You can only update your own profile")
        
        profile = self.user_service.get_user_profile(user_id)
        if not profile:
            raise NotFound("Profile not found")
        
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserProfileSerializer(profile).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)