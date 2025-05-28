from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from comments.exceptions import CommentNotFound
from comments.models import Comment
from posts.exceptions import PostNotFoundException
from posts.models import Post

from .repositories import VoteRepository
from .services import VoteService


@swagger_auto_schema(
    method='post',
    operation_summary="Upvote a post",
    operation_description="Adds an upvote to the specified post. If the user already upvoted," \
    " the vote is removed (toggle behavior). If the user previously downvoted, " \
    "the vote is changed to an upvote.",
    tags=["Votes"],
    responses={
        200: openapi.Response(
            description="Vote processed successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'post_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'action': openapi.Schema(type=openapi.TYPE_STRING, example="added",
                                              description="Action taken: 'added', " \
                                              "'removed', or 'changed'"),
                    'vote_type': openapi.Schema(type=openapi.TYPE_STRING, example="upvote"),
                    'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                    'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=3,
                                             description="Net score (upvotes minus downvotes)")
                }
            )
        ),
        401: openapi.Response(
            description="Unauthorized - Authentication required",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Authentication credentials were not provided."
                    )
                }
            )
        ),
        404: openapi.Response(
            description="Post not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Post with ID 999 not found"
                    )
                }
            )
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upvote_post(request, post_id: int):
    """Upvote a post"""
    try:
        result = VoteService.upvote_post(post_id, request.user)
        return Response(result, status=status.HTTP_200_OK)
    except PostNotFoundException:
        return Response(
            {"error": f"Post with ID {post_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Downvote a post",
    operation_description="Adds a downvote to the specified post. " \
    "If the user already downvoted, the vote is removed (toggle behavior)." \
    " If the user previously upvoted, the vote is changed to a downvote.",
    tags=["Votes"],
    responses={
        200: openapi.Response(
            description="Vote processed successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'post_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'action': openapi.Schema(type=openapi.TYPE_STRING, example="added", 
                                             description="Action taken: 'added', 'removed',"
                                             " or 'changed'"),
                    'vote_type': openapi.Schema(type=openapi.TYPE_STRING, example="downvote"),
                    'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                    'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=2, 
                                            description="Net score (upvotes minus downvotes)")
                }
            )
        ),
        401: openapi.Response(
            description="Unauthorized - Authentication required",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Authentication credentials were not provided."
                    )
                }
            )
        ),
        404: openapi.Response(
            description="Post not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Post with ID 999 not found"
                    )
                }
            )
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def downvote_post(request, post_id: int):
    """Downvote a post"""
    try:
        result = VoteService.downvote_post(post_id, request.user)
        return Response(result, status=status.HTTP_200_OK)
    except PostNotFoundException:
        return Response(
            {"error": f"Post with ID {post_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Upvote a comment",
    operation_description="Adds an upvote to the specified comment. " \
    "If the user already upvoted, the vote is removed (toggle behavior)." \
    " If the user previously downvoted, the vote is changed to an upvote.",
    tags=["Votes"],
    responses={
        200: openapi.Response(
            description="Vote processed successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'action': openapi.Schema(type=openapi.TYPE_STRING, example="added", 
                                             description="Action taken: 'added', 'removed',"
                                             " or 'changed'"),
                    'vote_type': openapi.Schema(type=openapi.TYPE_STRING, example="upvote"),
                    'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=2, 
                                            description="Net score (upvotes minus downvotes)")
                }
            )
        ),
        401: openapi.Response(
            description="Unauthorized - Authentication required",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Authentication credentials were not provided."
                    )
                }
            )
        ),
        404: openapi.Response(
            description="Comment not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Comment with ID 999 not found"
                    )
                }
            )
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upvote_comment(request, comment_id: int):
    """Upvote a comment"""
    try:
        result = VoteService.upvote_comment(comment_id, request.user)
        return Response(result, status=status.HTTP_200_OK)
    except CommentNotFound:
        return Response(
            {"error": f"Comment with ID {comment_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method='post',
    operation_summary="Downvote a comment",
    operation_description="Adds a downvote to the specified comment." \
    "If the user already downvoted, the vote is removed (toggle behavior)." \
    " If the user previously upvoted, the vote is changed to a downvote.",
    tags=["Votes"],
    responses={
        200: openapi.Response(
            description="Vote processed successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    'action': openapi.Schema(type=openapi.TYPE_STRING, example="added", 
                                             description="Action taken: 'added', " \
                                             "'removed', or 'changed'"),
                    'vote_type': openapi.Schema(type=openapi.TYPE_STRING, example="downvote"),
                    'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=1, 
                                            description="Net score (upvotes minus downvotes)")
                }
            )
        ),
        401: openapi.Response(
            description="Unauthorized - Authentication required",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Authentication credentials were not provided."
                    )
                }
            )
        ),
        404: openapi.Response(
            description="Comment not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Comment with ID 999 not found"
                    )
                }
            )
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def downvote_comment(request, comment_id: int):
    """Downvote a comment"""
    try:
        result = VoteService.downvote_comment(comment_id, request.user)
        return Response(result, status=status.HTTP_200_OK)
    except CommentNotFound:
        return Response(
            {"error": f"Comment with ID {comment_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get post vote counts",
    operation_description="Retrieves the number of upvotes, downvotes, and net score for a post." \
    " If the user is authenticated, also returns their current vote status.",
    tags=["Votes"],
    responses={
        200: openapi.Response(
            description="Vote counts retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                    'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=7),
                    'voted': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True, 
                                            description="Present only for authenticated users"),
                    'is_upvote': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True, 
                                                description="Present only for authenticated " \
                                                "users who have voted")
                }
            )
        ),
        404: openapi.Response(
            description="Post not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Post with ID 999 not found"
                    )
                }
            )
        )
    }
)
@api_view(['GET'])
def get_post_votes(request, post_id: int):
    """Get vote counts for a post"""
    try:
        # Check if post exists
        Post.objects.get(id=post_id)
        
        # Get vote data
        if request.user.is_authenticated:
            result = VoteService.get_post_vote_status(post_id, request.user.id)
        else:
            result = VoteRepository.get_post_votes(post_id)
            
        return Response(result, status=status.HTTP_200_OK)
    except Post.DoesNotExist:
        return Response(
            {"error": f"Post with ID {post_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )


@swagger_auto_schema(
    method='get',
    operation_summary="Get comment vote counts",
    operation_description="Retrieves the number of upvotes, " \
    "downvotes, and net score for a comment. If the user is " \
    "authenticated, also returns their current vote status.",
    tags=["Votes"],
    responses={
        200: openapi.Response(
            description="Vote counts retrieved successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'upvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
                    'downvotes': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
                    'score': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    'voted': openapi.Schema(type=openapi.TYPE_BOOLEAN, 
                                            example=True, 
                                            description="Present only for authenticated users"),
                    'is_upvote': openapi.Schema(type=openapi.TYPE_BOOLEAN, 
                                                example=False,
                                description="Present only for authenticated users who have voted")
                }
            )
        ),
        404: openapi.Response(
            description="Comment not found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Comment with ID 999 not found"
                    )
                }
            )
        )
    }
)
@api_view(['GET'])
def get_comment_votes(request, comment_id: int):
    """Get vote counts for a comment"""
    try:
        # Check if comment exists
        Comment.objects.get(id=comment_id)
        
        # Get vote data
        if request.user.is_authenticated:
            result = VoteService.get_comment_vote_status(comment_id, request.user.id)
        else:
            result = VoteRepository.get_comment_votes(comment_id)
            
        return Response(result, status=status.HTTP_200_OK)
    except Comment.DoesNotExist:
        return Response(
            {"error": f"Comment with ID {comment_id} not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )