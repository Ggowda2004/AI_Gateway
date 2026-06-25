class AuthError(Exception):
    """Custom exception class for authentication errors."""

    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code