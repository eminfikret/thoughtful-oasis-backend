from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from claims.services import ClaimService
from posts.models import Post

from .exceptions import CommentNotFound, PostNotFound
from .models import Comment
from .serializers import CreateCommentSerializer, PostCommentSerializer, ReplyCommentSerializer
from .services import CommentService


@swagger_auto_schema(
    operation_summary="Create a comment on a post",
    operation_description="Creates a new top-level comment on the specified post by post_id.",
    tags=["Comments"],
    request_body=CreateCommentSerializer,
    responses={
        201: openapi.Response(
            description="Comment created successfully",
            schema=PostCommentSerializer),
        400: openapi.Response(description="Invalid input"),
        401: openapi.Response(description="Unauthorized - Authentication required"),
        404: openapi.Response(description="Post not found"),
    },
)
class CreateCommentView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = CreateCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = CommentService.create_comment(
            post_id=serializer.validated_data['post_id'],
            author=request.user,
            content=serializer.validated_data['content']
        )

        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('comment', comment.id)

        response_data = PostCommentSerializer(comment).data
        response_data['claims'] = claims

        return Response(response_data, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    operation_summary="Reply to a comment",
    operation_description="Creates a reply to an existing comment using parent_comment_id.",
    tags=["Comments"],
    request_body=ReplyCommentSerializer,
    responses={
        201: openapi.Response(description="Reply created successfully",
                              schema=PostCommentSerializer),
        400: openapi.Response(description="Invalid input"),
        401: openapi.Response(description="Unauthorized - Authentication required"),
        404: openapi.Response(description="Parent comment not found"),
    },
)
class CreateReplyView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        serializer = ReplyCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = CommentService.create_reply(
            parent_comment_id=serializer.validated_data['parent_comment_id'],
            author=request.user,
            content=serializer.validated_data['content']
        )

        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('comment', comment.id)
        
        response_data = PostCommentSerializer(comment).data
        response_data['claims'] = claims

        return Response(response_data, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    operation_summary="Get all comments for a post",
    operation_description=
    "Fetches all top-level comments for a post, using post_id in the request body.",
    tags=["Comments"],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["post_id"],
        properties={
            "post_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the post"),
        },
    ),
    responses={
        200: openapi.Response(description="List of comments",
                              schema=PostCommentSerializer(many=True)),
        400: openapi.Response(description="Missing or invalid post_id"),
        404: openapi.Response(description="Post not found"),
    },
)

class PostCommentsView(views.APIView):
    def get(self, request):
        post_id = request.data.get('post_id')
        try:
            comments = CommentService.get_comments_for_post(post_id)
        except Post.DoesNotExist:
            raise PostNotFound()

        claim_service = ClaimService()
        response_data = []
        
        for comment in comments:
            comment_data = PostCommentSerializer(comment).data
            claims = claim_service.get_claims_for_content('comment', comment.id)
            comment_data['claims'] = claims
            response_data.append(comment_data)
            
        return Response(response_data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    operation_summary="Get replies to a comment",
    operation_description="Returns all replies for a given comment by comment_id (passed in URL).",
    tags=["Comments"],
    responses={
        200: openapi.Response(description="List of replies"
            , schema=PostCommentSerializer(many=True)),
        404: openapi.Response(description="Comment not found"),
    },
)

class CommentRepliesView(views.APIView):
    def get(self, request, comment_id):
        try:
            replies = CommentService.get_replies_for_comment(comment_id)
        except Comment.DoesNotExist:
            raise CommentNotFound()

        claim_service = ClaimService()
        response_data = []
        
        for reply in replies:
            reply_data = PostCommentSerializer(reply).data
            claims = claim_service.get_claims_for_content('comment', reply.id)
            reply_data['claims'] = claims
            response_data.append(reply_data)
            
        return Response(response_data, status=status.HTTP_200_OK)
