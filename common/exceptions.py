class UnauthorizedAccessException(Exception):
    def __init__(self, message: str = "You are not allowed to access this resource."):
        super().__init__(message)