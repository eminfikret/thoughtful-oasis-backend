from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.swagger_schemas import (
    login_response_schema,
    not_found_response,
    permission_denied_response,
    register_response_schema,
    token_refresh_schema,
    unauthorized_response,
    user_detail_schema,
    user_profile_schema,
    username_email_check_schema,
)

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
        tags=["Users"],
        responses={
            200: openapi.Response(
                description="List of users",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=user_detail_schema()
                )
            ),
            401: unauthorized_response()
        }
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
        operation_description="Register a new user with username, email, and password",
        tags=["Users"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password', 'password2', 'email'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, example="newuser"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, example="StrongP@ssword123"),
                'password2': openapi.Schema(type=openapi.TYPE_STRING, example="StrongP@ssword123"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, example="newuser@example.com"),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, example="John"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, example="Doe"),
            }
        ),
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=register_response_schema()
            ),
            400: openapi.Response(
                description="Bad Request - Invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'username': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["A user with that username already exists."]
                        ),
                        'email': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["A user with this email already exists."]
                        ),
                        'password': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Password fields didn't match."]
                        )
                    }
                )
            )
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
        operation_description="Login a user with username and password to receive " \
        "authentication tokens",
        tags=["Users"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, example="user123"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, example="password123")
            }
        ),
        responses={
            200: openapi.Response(
                description="Successful login",
                schema=login_response_schema()
            ),
            400: openapi.Response(
                description="Bad Request - Invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'username': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        ),
                        'password': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Invalid credentials",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Invalid credentials"
                        )
                    }
                )
            )
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
                    'token': result['access_token'],
                    'refresh_token': result['refresh_token']
                }, status=status.HTTP_200_OK)
            
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    @swagger_auto_schema(
        operation_summary="Refresh access token",
        operation_description="Refresh an access token using a valid refresh token",
        tags=["Users"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh_token'],
            properties={
                'refresh_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="New access token",
                schema=token_refresh_schema()
            ),
            400: openapi.Response(
                description="Bad Request - Missing refresh token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Refresh token is required"
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Invalid or expired refresh token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Invalid or expired refresh token"
                        )
                    }
                )
            )
        }
    )
    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"error": "Refresh token is required"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        user_service = UserService()
        tokens = user_service.refresh_token(refresh_token)

        if tokens is None:
            return Response({"error": "Invalid or expired refresh token"}, 
                            status=status.HTTP_401_UNAUTHORIZED)

        return Response(tokens, status=status.HTTP_200_OK)


class UserDetailController(APIView):
    """Controller for user detail operations"""
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()

    @swagger_auto_schema(
        operation_summary="Get user details",
        operation_description="Get detailed information for a specific user by ID",
        tags=["Users"],
        responses={
            200: openapi.Response(
                description="User details retrieved successfully",
                schema=user_detail_schema()
            ),
            401: unauthorized_response(),
            404: not_found_response("User not found")
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
        operation_description="Update details for a specific user "
        "(can only update your own details)",
        tags=["Users"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, example="Updated"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, example="Name"),
                'profile': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'bio': openapi.Schema(type=openapi.TYPE_STRING,
                                               example="Updated bio information"),
                        'website': openapi.Schema(type=openapi.TYPE_STRING, 
                                                  example="https://updated-site.com")
                    }
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="User details updated successfully",
                schema=user_detail_schema()
            ),
            400: openapi.Response(
                description="Bad Request - Invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'first_name': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is invalid."]
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            403: permission_denied_response("You can only update your own details"),
            404: not_found_response("User not found")
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
        operation_description="Get profile information for a specific user by ID",
        tags=["Users"],
        responses={
            200: openapi.Response(
                description="User profile retrieved successfully",
                schema=user_profile_schema()
            ),
            401: unauthorized_response(),
            404: not_found_response("Profile not found")
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
        operation_description="Update profile for a specific user "
        "(can only update your own profile)",
        tags=["Users"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'bio': openapi.Schema(type=openapi.TYPE_STRING, example="Updated bio information"),
                'website': openapi.Schema(type=openapi.TYPE_STRING, example="https://updated-site.com"),
                'profile_picture': openapi.Schema(type=openapi.TYPE_FILE, format="binary")
            }
        ),
        responses={
            200: openapi.Response(
                description="User profile updated successfully",
                schema=user_profile_schema()
            ),
            400: openapi.Response(
                description="Bad Request - Invalid data",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'website': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Enter a valid URL."]
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            403: permission_denied_response("You can only update your own profile"),
            404: not_found_response("Profile not found")
        }
    )
    def patch(self, request, user_id):
        """Update a specific user's profile"""
        # Only allow users to update their own profile
        if request.user.id != int(user_id):
            return Response({"error": "You can only update your own profile"}, 
                            status=status.HTTP_403_FORBIDDEN)

        profile = self.user_service.get_user_profile(user_id)
        if not profile:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserProfileSerializer(profile).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckUsernameEmailController(APIView):
    """Controller for checking if a username or email is already taken"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    @swagger_auto_schema(
        operation_summary="Check username/email availability",
        operation_description="Check if a username or email is already registered in the system",
        tags=["Users"],
        manual_parameters=[
            openapi.Parameter(
                name='username',
                in_=openapi.IN_QUERY,
                description='Username to check',
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                name='email',
                in_=openapi.IN_QUERY,
                description='Email to check',
                type=openapi.TYPE_STRING,
                required=False
            ),
        ],
        responses={
            200: openapi.Response(
                description="Check successful",
                schema=username_email_check_schema()
            ),
            400: openapi.Response(
                description="Bad request - Missing parameters",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Either username or email parameter is required"
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        """Check if username or email exists"""
        username = request.query_params.get('username')
        email = request.query_params.get('email')
        
        if not username and not email:
            return Response(
                {"error": "Either username or email parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        result = self.user_service.check_username_email_exists(username, email)
        return Response(result, status=status.HTTP_200_OK)


class UserDeleteController(APIView):
    """Controller for deleting a user account"""
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    @swagger_auto_schema(
        operation_summary="Delete user account",
        operation_description="Delete your own user account permanently",
        tags=["Users"],
        responses={
            204: openapi.Response(description="User deleted successfully"),
            401: unauthorized_response(),
            403: permission_denied_response("You can only delete your own account"),
            404: not_found_response("User not found"),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Failed to delete user"
                        )
                    }
                )
            )
        }
    )
    def delete(self, request, user_id):
        """Delete a user account"""
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.id != int(user_id):
            return Response(
                {"error": "You can only delete your own account"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        success = self.user_service.delete_user(user_id)
        if not success:
            return Response({"error": "Failed to delete user"}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(status=status.HTTP_204_NO_CONTENT)