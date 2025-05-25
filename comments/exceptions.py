from rest_framework.exceptions import APIException
from rest_framework import status

class CommentNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Comment not found."


class PostNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Post not found."


class InvalidReplyDepth(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Replies are only allowed one level deep."