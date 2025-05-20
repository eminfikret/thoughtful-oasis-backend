from rest_framework import status
from rest_framework.exceptions import APIException


class ConflictAPIException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict occurred."
    default_code = "conflict"