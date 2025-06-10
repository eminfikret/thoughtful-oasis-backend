from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, views
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from claims.services import ClaimService
from posts.models import Post
from common.swagger_schemas import (
    not_found_response,
    unauthorized_response,
    permission_denied_response,
    comment_example_response,
    comment_reply_example_response,
    comments_paginated_response
)

from .exceptions import CommentNotFound
from .models import Comment
from .serializers import (
    CommentUpdateSerializer,
    CreateCommentSerializer,
    PostCommentSerializer,
    ReplyCommentSerializer,
    UserCommentsQueryParamsSerializer,
)
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
                schema=comment_example_response()
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "post_id": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        ),
                        "content": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            404: not_found_response("Post not found"),
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

        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('comment', comment.id)

        response_data = PostCommentSerializer(comment, context={'request': request}).data
        response_data['claims'] = claims

        return Response(response_data, status=status.HTTP_201_CREATED)


class CreateReplyView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Reply to a comment",
        operation_description="Creates a reply to an existing comment using parent_comment_id.",
        tags=["Comments"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["parent_comment_id", "content"],
            properties={
                "parent_comment_id": openapi.Schema(type=openapi.TYPE_INTEGER, 
                                          description="ID of the parent comment"),
                "content": openapi.Schema(type=openapi.TYPE_STRING,
                                           description="Content of the comment"),
            },
            example={
                "parent_comment_id": 123,
                "content": "This is a reply comment."
            }
        ),
        responses={
            201: openapi.Response(
                description="Reply created successfully",
                schema=comment_reply_example_response()
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "parent_comment_id": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        ),
                        "content": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            404: not_found_response("Parent comment not found"),
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

        claim_service = ClaimService()
        claims = claim_service.get_claims_for_content('comment', comment.id)
        
        response_data = PostCommentSerializer(comment, context={'request': request}).data
        response_data['claims'] = claims

        return Response(response_data, status=status.HTTP_201_CREATED)

class PostCommentsView(views.APIView):
    @swagger_auto_schema(
        operation_summary="Get all comments for a post",
        operation_description="Fetches all top-level comments for a post, using post_id as a query parameter.",
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
            200: openapi.Response(
                description="List of comments", 
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=comment_example_response()
                )
            ),
            400: openapi.Response(
                description="Missing post_id", 
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            example="Missing post_id parameter"
                        )
                    }
                )
            ),
            404: not_found_response("Post not found"),
        },
    )
    def get(self, request):
        post_id = request.query_params.get('post_id')
        if not post_id:
            return Response({"error": "Missing post_id parameter"}, 
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            get_object_or_404(Post, id=post_id) 
            comments = CommentService.get_comments_for_post(post_id)
            
            claim_service = ClaimService()
            response_data = []
            
            for comment in comments:
                comment_data = PostCommentSerializer(comment, context={'request': request}).data
                claims = claim_service.get_claims_for_content('comment', comment.id)
                comment_data['claims'] = claims
                response_data.append(comment_data)
                
            return Response(response_data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method="get",
    operation_summary="Get replies to a comment",
    operation_description="Returns all replies for a given comment by comment_id (passed in URL).",
    tags=["Comments"],
    responses={
        200: openapi.Response(description="List of replies",
                              schema=PostCommentSerializer(many=True)),
        404: openapi.Response(description="Comment not found"),
    },
)
@api_view(['GET'])
def get_comment_replies(request, comment_id):
    get_object_or_404(Comment, id=comment_id)

    try:
        replies = CommentService.get_replies_for_comment(comment_id)
    except Comment.DoesNotExist:
        raise CommentNotFound()

    claim_service = ClaimService()
    response_data = []
    
    for reply in replies:
        reply_data = PostCommentSerializer(reply, context={'request': request}).data
        claims = claim_service.get_claims_for_content('comment', reply.id)
        reply_data['claims'] = claims
        response_data.append(reply_data)
        
    return Response(response_data, status=status.HTTP_200_OK)


class CommentRepliesView(views.APIView):
    @swagger_auto_schema(
        operation_summary="Get replies to a comment",
        operation_description="Returns all replies for a given comment by comment_id (passed in URL).",
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
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=comment_reply_example_response()
                )
            ),
            404: not_found_response("Comment not found"),
        },
    )
    def get(self, request, comment_id):
        get_object_or_404(Comment, id=comment_id)

        try:
            replies = CommentService.get_replies_for_comment(comment_id)
        except Comment.DoesNotExist:
            raise CommentNotFound()

        claim_service = ClaimService()
        response_data = []
        
        for reply in replies:
            reply_data = PostCommentSerializer(reply, context={'request': request}).data
            claims = claim_service.get_claims_for_content('comment', reply.id)
            reply_data['claims'] = claims
            response_data.append(reply_data)
            
        return Response(response_data, status=status.HTTP_200_OK)

class UpdateCommentView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Update a comment",
        operation_description="Updates content of an existing comment. User can only update their own comments.",
        tags=["Comments"],
        request_body=CommentUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Comment updated successfully",
                schema=comment_example_response()
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT, 
                    properties={
                        "content": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            403: permission_denied_response("You can only update your own comments"),
            404: not_found_response("Comment not found"),
        },
    )
    def put(self, request, comment_id):
        serializer = CommentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            use_mock_llm = request.data.get('use_mock_llm', False)
            
            comment = CommentService.update_comment(
                comment_id=comment_id,
                user=request.user,
                content=serializer.validated_data['content']
            )
            
            comment.use_mock_llm = use_mock_llm
            comment.save()
            
            claim_service = ClaimService()
            claims = claim_service.get_claims_for_content('comment', comment.id)
            
            response_data = PostCommentSerializer(comment, context={'request': request}).data
            response_data['claims'] = claims
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except CommentNotFound:
            return Response({"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND)
        except PermissionDenied as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)

class UserCommentsView(views.APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    @swagger_auto_schema(
        operation_summary="Get all comments by a user",
        operation_description="Retrieves all comments made by a specific user. Supports pagination.",
        tags=["Comments"],
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
                description="Number of comments to return",
                required=False,
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                name="offset",
                in_=openapi.IN_QUERY,
                description="Number of comments to skip",
                required=False,
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="User comments retrieved successfully",
                schema=comments_paginated_response()
            ),
            400: openapi.Response(
                description="Missing or invalid parameters",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user_id": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                            example=["This field is required."]
                        )
                    }
                )
            ),
            401: unauthorized_response(),
            404: not_found_response("User not found"),
        }
    )
    def get(self, request):
        serializer = UserCommentsQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        user_id = serializer.validated_data['user_id']
        offset = serializer.validated_data.get('offset', 0)
        limit = serializer.validated_data.get('limit', 10)
        
        try:
            comments, total = CommentService.get_user_comments(user_id, offset, limit)
            
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
            
            for comment in comments:
                comment_data = PostCommentSerializer(comment, context={'request': request}).data
                claims = claim_service.get_claims_for_content('comment', comment.id)
                comment_data['claims'] = claims
                results.append(comment_data)
                
            return Response({
                'count': total,
                'next': next_url,
                'previous': previous_url,
                'results': results
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)