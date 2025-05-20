from typing import Optional

from common.exceptions import PermissionDeniedException


class SubscriptionPermissionDeniedException(PermissionDeniedException):
    def __init__(self, error: Optional[str] = "You do not have permission to view subscribers."):
        super().__init__(error)