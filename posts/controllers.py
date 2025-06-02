from django.db import IntegrityError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound as NotFoundAPIException
from rest_framework.exceptions import PermissionDenied as PermissionDeniedAPIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from claims.services import ClaimService
from common.exceptions import NotFoundException, PermissionDeniedException
from common.params import PaginationParams
from common.responses import PaginatedResponse
from posts.dtos import CreatePostDto, UpdatePostDto
from posts.exceptions import PostNotFoundException, UnauthorizedPostAccessException
from posts.models import Post
from posts.serializers import (
    PostCreateSerializer,
    PostSerializer,
    PostsQueryParamsSerializer,
    PostUpdateSerializer,
)
from posts.services import PostService
from posts.types import PostId


class ChannelPostsController(APIView):
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
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "count": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema( type=openapi.TYPE_OBJECT,
                                                  properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "channel_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "author_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "title": openapi.Schema(type=openapi.TYPE_STRING),
                                        "content": openapi.Schema(type=openapi.TYPE_STRING),
                                        "created_at": openapi.Schema(type=openapi.TYPE_STRING,
                                                                      format="date-time"),
                                        "updated_at": openapi.Schema(type=openapi.TYPE_STRING,
                                                                      format="date-time"),
                                                  })
                        )
                    }
                )
            ),
            401: openapi.Response(description="Unauthorized"),
            403: openapi.Response(description="Permission denied"),
            404: openapi.Response(description="Channel not found"),
        }
    )
    def get(self, request, pk: int):
        params = PostsQueryParamsSerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        data = params.validated_data

        limit = data.get('limit') if data.get('limit') is not None else 10
        offset = data.get('offset') if data.get('offset') is not None else 0

        pagination = PaginationParams(limit=limit, offset=offset)
        search = data.get('search')

        try:
            posts = PostService.get_posts_by_channel(
                channel_id=pk,
                requester=request.user,
                pagination=pagination,
                search=search
            )
            count = PostService.get_posts_count_by_channel( channel_id=pk,search=search)
        except NotFoundException as e:
            raise NotFoundAPIException(detail=str(e))
        except PermissionDeniedException as e:
            raise PermissionDeniedAPIException(detail=str(e))

        return PaginatedResponse(
            results=PostSerializer(posts, many=True).data,
            count=count,
            request=request
        )


    @swagger_auto_schema(
        method="post",
        operation_summary="Create a new post",
        operation_description="Creates a post in the specified channel. Requires authentication.",
        tags=["Posts"],
        request_body=PostCreateSerializer,
        responses={
            201: openapi.Response(
                description="Post created",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT,
                                       properties={
                                           "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                           "channel_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                           "author_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                           "title": openapi.Schema(type=openapi.TYPE_STRING),
                                           "content": openapi.Schema(type=openapi.TYPE_STRING),
                                           "created_at": openapi.Schema(type=openapi.TYPE_STRING,
                                                                         format="date-time"),
                                           "updated_at": openapi.Schema(type=openapi.TYPE_STRING, 
                                                                        format="date-time"),
                                       })
            ),
            400: openapi.Response(description="Invalid input or invalid channel ID"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="Channel not found"),
        }
    )
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    def create_post(request):
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dto = CreatePostDto(**serializer.validated_data)
        try:
                post = PostService.create_post(dto, author=request.user)
        except IntegrityError:
            return Response({"error": "Invalid channel ID"}, 
                            status=status.HTTP_400_BAD_REQUEST)
        out = PostSerializer(post)
        return Response(out.data, status=status.HTTP_201_CREATED)


    @swagger_auto_schema(
        method="get",
        operation_summary="Retrieve a post",
        operation_description="Fetches a post by its ID.",
        tags=["Posts"],
        responses={
            200: openapi.Response(description="Post data", 
                                  schema=openapi.Schema( type=openapi.TYPE_OBJECT,
                                        properties={
                                            "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "channel_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "author_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "title": openapi.Schema(type=openapi.TYPE_STRING),
                                        "content": openapi.Schema(type=openapi.TYPE_STRING),
                                        "created_at": openapi.Schema(type=openapi.TYPE_STRING,
                                                                      format="date-time"),
                                        "updated_at": openapi.Schema(type=openapi.TYPE_STRING,
                                                                      format="date-time"),
                                                                                  })),
            404: openapi.Response(description="Post not found"),
        }
    )
    @api_view(['GET'])
    def get_post(request, post_id: int):
        try:
            post = PostService.get_post_by_id(PostId(post_id))
            return Response(PostSerializer(post).data)
        except PostNotFoundException:
            raise NotFoundAPIException(detail="Post not found")


# ─── Delete Post ─────────────────────────────────────────────────────────────────

@swagger_auto_schema(
    method="delete",
    operation_summary="Delete a post",
    operation_description="Deletes a post by its ID. Requires authentication.",
    tags=["Posts"],
    responses={
        204: openapi.Response(description="Deleted successfully"),
        401: openapi.Response(description="Unauthorized"),
        403: openapi.Response(description="Forbidden"),
        404: openapi.Response(description="Post not found"),
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


@api_view(['GET'])
def list_posts(request):
    serializer = PostsQueryParamsSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    posts = PostService.get_all_posts(serializer.validated_data)
    serializer = PostSerializer(posts, many=True)

    return Response(serializer.data)


class PostDetailController(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Update a post",
        operation_description="Updates title/content of an existing post. Requires authentication.",
        tags=["Posts"],
        request_body=PostUpdateSerializer,
        responses={
            200: openapi.Response(description="Updated post",
                                schema=openapi.Schema( type=openapi.TYPE_OBJECT,
                                    properties={
                                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "channel_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "author_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                        "title": openapi.Schema(type=openapi.TYPE_STRING),
                                        "content": openapi.Schema(type=openapi.TYPE_STRING),
                                        "created_at": openapi.Schema(type=openapi.TYPE_STRING, 
                                                                     format="date-time"),
                                         "updated_at": openapi.Schema(type=openapi.TYPE_STRING, 
                                                                      format="date-time"),
                                                                                     })),
            400: openapi.Response(description="Invalid input"),
            401: openapi.Response(description="Unauthorized"),
            403: openapi.Response(description="Forbidden"),
            404: openapi.Response(description="Post not found"),
        }
    )
    def put(self, request, post_id: int):
        serializer = PostUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        dto = UpdatePostDto(**serializer.validated_data)

        try:
            post = PostService.update_post(PostId(post_id), dto, request.user)
            
            claim_service = ClaimService()
            claims = claim_service.get_claims_for_content('post', post.id)
            
            response_data = PostSerializer(post).data
            response_data['claims'] = claims
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            raise NotFoundAPIException(detail="Post not found")
        except UnauthorizedPostAccessException:
            raise PermissionDeniedAPIException(detail="Forbidden")
        except NotFoundException as e:
            raise NotFoundAPIException(detail=str(e))
        except PermissionDeniedException as e:
            raise PermissionDeniedAPIException(detail=str(e))

