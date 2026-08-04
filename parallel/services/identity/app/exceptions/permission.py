from fastapi import status

from app.exceptions.exceptions import ParallelException


class PermissionAlreadyExistsException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="PERMISSION_001",
            message="Permission already exists",
        )


class PermissionNotFoundException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="PERMISSION_002",
            message="Permission not found",
        )


class PermissionDeniedException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="PERMISSION_003",
            message="You do not have permission to perform this action",
        )
