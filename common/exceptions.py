class PermissionDeniedException(Exception):
    """Base exception for permission denied."""
    def __init__(self, error="Permission denied."):
        self.error = error 
        super().__init__(error)

class ConflictException(Exception):
    """Base exception for conflicts."""
    def __init__(self, error: str = "Conflict occurred with an existing resource."):
        self.error = error
        super().__init__(error)

class NotFoundException(Exception):
    """Base exception for not found resources."""
    def __init__(self, error: str = "Resource not found."):
        self.error = error
        super().__init__(error)