from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from posts.dtos import CreatePostDto, UpdatePostDto
from posts.exceptions import PostNotFoundException, UnauthorizedPostAccessException
from posts.params import PostsParams
from posts.serializers import (
    PostSerializer,
    PostCreateSerializer,
    PostUpdateSerializer,
    PostsQueryParamsSerializer,
)
from posts.services import PostService
from posts.types import PostId


@api_view(['GET'])
def list_posts(request):
    serializer = PostsQueryParamsSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)

    posts = PostService.get_all_posts(serializer.validated_data)
    serializer = PostSerializer(posts, many=True)

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    serializer = PostCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    dto = CreatePostDto(
        channel_id=serializer.validated_data['channel_id'],
        title=serializer.validated_data['title'],
        content=serializer.validated_data['content'],
    )

    post = PostService.create_post(dto, author=request.user)

    serializer = PostSerializer(post)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_post(request, post_id: int):
    try:
        post = PostService.get_post_by_id(PostId(post_id))
        serializer = PostSerializer(post)
        return Response(serializer.data)
    except PostNotFoundException:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_post(request, post_id: int):
    serializer = PostUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    dto = UpdatePostDto(
        title=serializer.validated_data.get('title'),
        content=serializer.validated_data.get('content'),
    )

    try:
        post = PostService.update_post(PostId(post_id), dto, request.user)
        serializer = PostSerializer(post)
        return Response(serializer.data)
    except PostNotFoundException:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
    except UnauthorizedPostAccessException:
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post(request, post_id: int):
    try:
        PostService.delete_post(PostId(post_id), request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except PostNotFoundException:
        return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)
    except UnauthorizedPostAccessException:
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)