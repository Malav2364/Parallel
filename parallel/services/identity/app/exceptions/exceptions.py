class ParallelException(Exception):
    """Base exception for Parallel."""

    def __init__(self, message: str, status_code: int, error_code: str):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)


class ResourceNotFoundException(ParallelException):
    def __init__(self, resource: str):
        super().__init__(
            message=f"{resource} not found",
            status_code=404,
            error_code="RESOURCE_NOT_FOUND",
        )


class BadRequestException(ParallelException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BAD_REQUEST",
        )
