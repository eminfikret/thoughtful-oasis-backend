class PermissionDeniedException(Exception):
    """Base exception for permission denied."""
    def __init__(self, message="Permission denied."):
        super().__init__(message)

class ConflictException(Exception):
    """Base exception for conflicts."""
    def __init__(self, message: str = "Conflict occurred with an existing resource."):
        super().__init__(message)

class NotFoundException(Exception):
    """Base exception for not found resources."""
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message)


