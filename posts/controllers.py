from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound as NotFoundAPIException
from rest_framework.exceptions import PermissionDenied as PermissionDeniedAPIException
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from channels.types import ChannelId
from claims.services import ClaimService
from common.exceptions import NotFoundException, PermissionDeniedException
from common.params import PaginationParams
from common.responses import PaginatedResponse
from posts.dtos import CreatePostDto, UpdatePostDto
from posts.exceptions import PostNotFoundException, UnauthorizedPostAccessException
from posts.serializers import (
    PostCreateSerializer,
    PostSerializer,
    PostsQueryParamsSerializer,
    PostUpdateSerializer,
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
class ChannelPostsController(APIView):
    def get(self, request: Request, pk: ChannelId):
        query_serializer = PostsQueryParamsSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        try:
            posts = PostService.get_posts_by_channel(
                channel_id=pk,
                requester=request.user,
                pagination=PaginationParams(limit=params.get('limit'), offset=params.get('offset')),
                search=params.get('search')
            )
            count = PostService.get_posts_count_by_channel(
                channel_id=pk,
                requester=request.user,
                search=params.get('search')
            )
        except NotFoundException as e:
            raise NotFoundAPIException(detail=str(e))
        except PermissionDeniedException as e:
            raise PermissionDeniedAPIException(detail=str(e))

        serializer = PostSerializer(posts, many=True)
        return PaginatedResponse(
            results=serializer.data,
            count=count,
            request=request
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    serializer = PostCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dto = CreatePostDto(**serializer.validated_data)

    try:
        post = PostService.create_post(dto, author=request.user)
        
        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('post', post.id)
        
        response_data = PostSerializer(post).data
        response_data['claims'] = claims
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    except PermissionDeniedException as e:
        raise PermissionDeniedAPIException(detail=str(e))


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
    dto = UpdatePostDto(**serializer.validated_data)

    try:
        post = PostService.update_post(post_id, dto, request.user)

        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('post', post.id)

        response_data = PostSerializer(post).data
        response_data['claims'] = claims
        
        return Response(response_data, status=status.HTTP_200_OK)
    except NotFoundException as e:
        raise NotFoundAPIException(detail=str(e))
    except PermissionDeniedException as e:
        raise PermissionDeniedAPIException(detail=str(e))


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