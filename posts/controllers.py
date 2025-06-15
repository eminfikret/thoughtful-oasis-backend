from django.contrib.auth.models import User
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound as NotFoundAPIException
from rest_framework.exceptions import PermissionDenied as PermissionDeniedAPIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from channels.exceptions import ChannelNotFoundException
from channels.services import ChannelService
from claims.services import ClaimService
from common.exceptions import NotFoundException, PermissionDeniedException
from common.params import PaginationParams
from common.responses import PaginatedResponse
from common.swagger_schemas import (
    not_found_response,
    permission_denied_response,
    post_detail_response,
    post_example_response,
    posts_paginated_response,
    unauthorized_response,
)
from posts.dtos import CreatePostDto, UpdatePostDto
from posts.exceptions import PostNotFoundException, UnauthorizedPostAccessException
from posts.models import Post
from posts.serializers import PostCreateSerializer as CreatePostSerializer
from posts.serializers import (
    PostSerializer,
    PostsQueryParamsSerializer,
    PostUpdateSerializer,
    UserPostsQueryParamsSerializer,
)
from posts.services import PostService
from posts.types import PostId


class ChannelPostsController(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="List posts in a channel",
        operation_description="Returns posts in the specified channel.",
        tags=["Posts"],
        manual_parameters=[
            openapi.Parameter("limit", openapi.IN_QUERY, "Page size", 
                            type=openapi.TYPE_INTEGER, default=10),
            openapi.Parameter("offset", openapi.IN_QUERY, "Pagination offset", 
                            type=openapi.TYPE_INTEGER, default=0),
            openapi.Parameter("search", openapi.IN_QUERY, "Search term", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="Paginated list of posts",
                schema=posts_paginated_response()
            ),
            401: unauthorized_response(),
            403: permission_denied_response(),
            404: not_found_response("Channel not found"),
        }
    )
    def get(self, request, pk: int):
        search = request.query_params.get('search')

        params = PostsQueryParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        limit = data.get('limit') if data.get('limit') is not None else 10
        offset = data.get('offset') if data.get('offset') is not None else 0

        pagination = PaginationParams(limit=limit, offset=offset)

        try:

            if search:

                channel = ChannelService.get_channel_by_id(pk)
                if not channel:
                    raise NotFoundException(f"Channel with ID {pk} not found")
                    
                channel_posts = Post.objects.filter(channel=channel)
                matching_posts = [
                    post for post in channel_posts 
                    if (search.lower() in post.title.lower() or 
                        search.lower() in post.content.lower())
                ]
                
                if not matching_posts:
                    return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            
            posts = PostService.get_posts_by_channel(
                channel_id=pk,
                requester=request.user,
                pagination=pagination,
                search=search
            )
                
            count = PostService.get_posts_count_by_channel(channel_id=pk, search=search)
        
            return PaginatedResponse(
                results=PostSerializer(posts, many=True, context={'request': request}).data,
                count=count,
                request=request
            )
            
        except NotFoundException as e:
            raise NotFoundAPIException(detail=str(e))
        except PermissionDeniedException as e:
            raise PermissionDeniedAPIException(detail=str(e))
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@swagger_auto_schema(
    method='post',
    operation_summary="Create a post",
    operation_description="Create a new post in the specified channel.",
    tags=["Posts"],
    request_body=CreatePostSerializer,
    responses={
        201: openapi.Response(
            description="Post created successfully",
            schema=post_example_response()
        ),
        400: openapi.Response(
            description="Bad request - Invalid data",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'title': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        example=["This field is required."]
                    ),
                    'content': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        example=["This field is required."]
                    ),
                    'channel_id': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_STRING),
                        example=["This field is required."]
                    )
                }
            )
        ),
        401: unauthorized_response(),
        404: not_found_response("Channel not found"),
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    serializer = CreatePostSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        post = PostService.create_post(
            CreatePostDto(
                channel_id=serializer.validated_data['channel_id'],
                title=serializer.validated_data['title'],
                content=serializer.validated_data['content']
            ),
            author=request.user
        )
        
        response_data = PostSerializer(post, context={'request': request}).data
        
        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('post', post.id)
        response_data['claims'] = claims
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    except ChannelNotFoundException:
        return Response(
            {"error": "Channel not found"},
            status=status.HTTP_404_NOT_FOUND
        )

@swagger_auto_schema(
    method="delete",
    operation_summary="Delete a post",
    operation_description="Deletes a post by its ID. Requires authentication.",
    tags=["Posts"],
    responses={
        204: openapi.Response(description="Deleted successfully"),
        401: unauthorized_response(),
        403: permission_denied_response("You don't have permission to delete this post"),
        404: not_found_response("Post not found"),
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post(request, post_id: int):
    try:
        PostService.delete_post(PostId(post_id), request.user)
    except PostNotFoundException:
        raise NotFoundAPIException(detail="Post not found")
    except UnauthorizedPostAccessException:
        raise PermissionDeniedAPIException(detail="Forbidden")

    return Response(status=status.HTTP_204_NO_CONTENT)

class PostDetailController(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Update a post",
        operation_description="Updates title/content of an existing post. Requires authentication.",
        tags=["Posts"],
        request_body=PostUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Updated post",
                schema=post_example_response()
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'title': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["Ensure this field has no more than 255 characters."]
                        ),
                        'content': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field may not be blank."]
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            403: permission_denied_response("You can only update your own posts"),
            404: not_found_response("Post not found"),
        }
    )
    def put(self, request, post_id: int):
        serializer = PostUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dto = UpdatePostDto(**serializer.validated_data)
        use_mock_llm = request.data.get('use_mock_llm', False)

        try:
            try:
                post = PostService.get_post_by_id(PostId(post_id))
            except PostNotFoundException:
                return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        
            if not (post.author == request.user):
                return Response(
                    {"error": "Forbidden - You can only update your own posts"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            post.use_mock_llm = use_mock_llm
            
            updated_post = PostService.update_post(PostId(post_id), dto, request.user)
        
            claim_service = ClaimService()
            claims = claim_service.get_claims_for_content('post', post.id)
            
            response_data = PostSerializer(updated_post, context={'request': request}).data
            response_data['claims'] = claims
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
        except UnauthorizedPostAccessException:
            return Response({"error": "Forbidden - You cannot update this post"},
                             status=status.HTTP_403_FORBIDDEN)
        except NotFoundException as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDeniedException as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response(
                {"error": "An error occurred while updating the post"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@swagger_auto_schema(
    method="get",
    operation_summary="List all posts",
    operation_description="Returns a paginated list of all posts across all channels.",
    tags=["Posts"],
    manual_parameters=[
        openapi.Parameter("limit", openapi.IN_QUERY, "Page size", 
                          type=openapi.TYPE_INTEGER, default=10),
        openapi.Parameter("offset", openapi.IN_QUERY, "Pagination offset", 
                          type=openapi.TYPE_INTEGER, default=0),
        openapi.Parameter("search", openapi.IN_QUERY, "Search term", type=openapi.TYPE_STRING),
    ],
    responses={
        200: openapi.Response(
            description="Paginated list of posts",
            schema=posts_paginated_response()
        ),
        401: unauthorized_response(),
        404: not_found_response("No posts found"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def list_posts(request):
    """Get all posts with optional pagination and search"""
    try:
        search = request.query_params.get('search')

        params = PostsQueryParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        limit = data.get('limit') if data.get('limit') is not None else 10
        offset = data.get('offset') if data.get('offset') is not None else 0
        
        pagination = PaginationParams(limit=limit, offset=offset)

        posts = PostService.get_all_posts(pagination, search)
        count = PostService.get_posts_count(search)
        
        return PaginatedResponse(
            results=PostSerializer(posts, many=True, context={'request': request}).data,
            count=count,
            request=request
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@swagger_auto_schema(
    method="get",
    operation_summary="Get post details",
    operation_description="Returns the details of a specific post by ID, including XML" \
    " representation with claim links.",
    tags=["Posts"],
    responses={
        200: openapi.Response(
            description="Post details retrieved successfully",
            schema=post_detail_response() 
        ),
        401: unauthorized_response(),
        404: not_found_response("Post not found"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated]) 
def get_post_details(request, post_id): 
    try:
        post = PostService.get_post_by_id(PostId(post_id))
        
        if not post:
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = PostSerializer(post, context={'request': request})
        response_data = serializer.data
        
        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('post', post.id)
        response_data['claims'] = claims
        
        if claims:
            if post.claims_xml:
                response_data['claims_xml'] = post.claims_xml
            else:
                from claims.utils import generate_claim_linked_xml
                xml_content = generate_claim_linked_xml(post.content, claims)
                
                post.claims_xml = xml_content
                post.save(update_fields=['claims_xml'])
                
                response_data['claims_xml'] = xml_content
        else:
            response_data['claims_xml'] = f"<text>{post.content}</text>"
        
        return Response(response_data)
    except Exception as e:
        return Response({"error": f"Not found: {str(e)}"}, status=status.HTTP_404_NOT_FOUND)

class UserPostsView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get all posts by a user",
        operation_description="Retrieves all posts created by a specific user. " \
        "Supports pagination.",
        tags=["Posts"],
        manual_parameters=[
            openapi.Parameter(
                name="user_id",
                in_=openapi.IN_QUERY,
                description="ID of the user",
                required=True,
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                name="limit",
                in_=openapi.IN_QUERY,
                description="Number of posts to return",
                required=False,
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                name="offset",
                in_=openapi.IN_QUERY,
                description="Number of posts to skip",
                required=False,
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="User posts retrieved successfully",
                schema=posts_paginated_response()
            ),
            400: openapi.Response(description="Missing or invalid parameters"),
            401: unauthorized_response(),
            404: not_found_response("User not found")
        }
    )
    def get(self, request):
        serializer = UserPostsQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        offset = serializer.validated_data.get('offset', 0)
        limit = serializer.validated_data.get('limit', 10)
        
        try:
            posts, total = PostService.get_user_posts(user_id, offset, limit)
            
            next_url = None
            previous_url = None
            
            if offset + limit < total:
                next_url = request.build_absolute_uri(
                    f'?user_id={user_id}&offset={offset+limit}&limit={limit}'
                )
                
            if offset > 0:
                prev_offset = max(0, offset - limit)
                previous_url = request.build_absolute_uri(
                    f'?user_id={user_id}&offset={prev_offset}&limit={limit}'
                )
                
            claim_service = ClaimService()
            results = []
            
            for post in posts:
                post_data = PostSerializer(post, context={'request': request}).data
                claims = claim_service.get_claims_for_content('post', post.id)
                post_data['claims'] = claims
                results.append(post_data)
                
            return Response({
                'count': total,
                'next': next_url,
                'previous': previous_url,
                'results': results
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class HomePagePostsView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get top posts for homepage",
        operation_description="Returns highest-scoring posts across all channels " \
        "for the homepage. Default time window is 5 days.",
        tags=["Posts"],
        manual_parameters=[
            openapi.Parameter("limit", openapi.IN_QUERY, "Page size", 
                            type=openapi.TYPE_INTEGER, default=10),
            openapi.Parameter("offset", openapi.IN_QUERY, "Pagination offset", 
                            type=openapi.TYPE_INTEGER, default=0),
            openapi.Parameter("days", openapi.IN_QUERY, "Number of days to look back", 
                            type=openapi.TYPE_INTEGER, default=5),
        ],
        responses={
            200: openapi.Response(
                description="Top-voted posts",
                schema=posts_paginated_response()
            ),
            400: openapi.Response(
                description="Invalid parameters",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Days parameter must be positive"
                        )
                    }
                )
            ),
            401: unauthorized_response()
        }
    )
    def get(self, request):
        offset = int(request.query_params.get('offset', 0))
        limit = int(request.query_params.get('limit', 10))
        try:
            days = int(request.query_params.get('days', 5))
            if days <= 0:
                return Response(
                    {"error": "Days parameter must be positive"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValueError:
            return Response(
                {"error": "Days parameter must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            posts, total = PostService.get_top_posts(offset, limit, days)
            next_url = None
            previous_url = None
            
            if offset + limit < total:
                next_url = request.build_absolute_uri(
                    f'?offset={offset+limit}&limit={limit}&days={days}'
                )
            
            if offset > 0:
                prev_offset = max(0, offset - limit)
                previous_url = request.build_absolute_uri(
                    f'?offset={prev_offset}&limit={limit}&days={days}'
                )
            
            claim_service = ClaimService()
            results = []
            
            for post in posts:
                post_data = PostSerializer(post, context={'request': request}).data
                claims = claim_service.get_claims_for_content('post', post.id)
                post_data['claims'] = claims
                results.append(post_data)
                
            return Response({
                'count': total,
                'next': next_url,
                'previous': previous_url,
                'results': results
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )