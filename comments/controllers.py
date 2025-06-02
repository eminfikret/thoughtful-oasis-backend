from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from posts.models import Post

from .exceptions import CommentNotFound, PostNotFound
from .models import Comment
from .serializers import CreateCommentSerializer, PostCommentSerializer, ReplyCommentSerializer
from .services import CommentService


class CreateCommentView(views.APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    @swagger_auto_schema(
        operation_summary="Create a comment on a post",
        operation_description="Creates a new top-level comment on the specified post by post_id.",
        tags=["Comments"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["post_id", "content"],
            properties={
                "post_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the post"),
                "content": openapi.Schema(type=openapi.TYPE_STRING, 
                                          description="Content of the comment"),
            },
            example={
                "post_id": 123,
                "content": "This is a sample comment."
            }
        ),
        responses={
            201: openapi.Response(
                description="Comment created successfully",
                schema=PostCommentSerializer),
            400: openapi.Response(description="Invalid input"),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            404: openapi.Response(description="Post not found"),
        },
    )
    def post(self, request):
        serializer = CreateCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = CommentService.create_comment(
            post_id=serializer.validated_data['post_id'],
            author=request.user,
            content=serializer.validated_data['content']
        )

        return Response(PostCommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CreateReplyView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    @swagger_auto_schema(
        operation_summary="Reply to a comment",
        operation_description="Creates a reply to an existing comment using parent_comment_id.",
        tags=["Comments"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["post_id", "content"],
            properties={
                "post_id": openapi.Schema(type=openapi.TYPE_INTEGER, 
                                          description="ID of the post"),
                "content": openapi.Schema(type=openapi.TYPE_STRING,
                                           description="Content of the comment"),
            },
            example={
                "post_id": 123,
                "content": "This is an updated sample comment."
            }
        ),
        responses={
            201: openapi.Response(
                description="Reply created successfully",
                schema=PostCommentSerializer
            ),
            400: openapi.Response(description="Invalid input"),
            401: openapi.Response(description="Unauthorized - Authentication required"),
            404: openapi.Response(description="Parent comment not found"),
        },
    )
    def post(self, request):
        serializer = ReplyCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = CommentService.create_reply(
            parent_comment_id=serializer.validated_data['parent_comment_id'],
            author=request.user,
            content=serializer.validated_data['content']
        )

        return Response(PostCommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class PostCommentsView(views.APIView):
    @swagger_auto_schema(
        operation_summary="Get all comments for a post",
        operation_description="Fetches all top-level comments for a" \
        " post, using post_id as a query parameter.",
        tags=["Comments"],
        manual_parameters=[
            openapi.Parameter(
                name="post_id",
                in_=openapi.IN_QUERY,
                description="ID of the post",
                required=True,
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(description="List of comments",
                                   schema=PostCommentSerializer(many=True)),
            400: openapi.Response(description="Missing or invalid post_id"),
            404: openapi.Response(description="Post not found"),
        },
    )
    def get(self, request):
        post_id = request.data.get('post_id')
        try:
            comments = CommentService.get_comments_for_post(post_id)
        except Post.DoesNotExist:
            raise PostNotFound()

        serializer = PostCommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentRepliesView(views.APIView):
    @swagger_auto_schema(
        operation_summary="Get replies to a comment",
        operation_description="Returns all replies for a given" \
        " comment by comment_id (passed in URL).",
        tags=["Comments"],
        manual_parameters=[
            openapi.Parameter(
                name="comment_id",
                in_=openapi.IN_PATH,
                type=openapi.TYPE_INTEGER,
                description="ID of the parent comment to get replies for",
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="List of replies",
                schema=PostCommentSerializer(many=True)
            ),
            404: openapi.Response(description="Comment not found"),
        },
    )
    def get(self, request, comment_id):
        get_object_or_404(Comment, id=comment_id)

        try:
            replies = CommentService.get_replies_for_comment(comment_id)
        except Comment.DoesNotExist:
            raise CommentNotFound()

        serializer = PostCommentSerializer(replies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
