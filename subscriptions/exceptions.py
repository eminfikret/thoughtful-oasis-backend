from typing import Optional

from common.exceptions import UnauthorizedAccessException


class UnauthorizedSubscriptionAccessException(UnauthorizedAccessException):
    def __init__(self, message: Optional[str] = "You do not have permission to view subscribers."):
        super().__init__(message)