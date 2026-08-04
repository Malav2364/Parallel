from fastapi import status

from app.exceptions.exceptions import ParallelException


class RoleAlreadyExistsException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="ROLE_001",
            message="Role already exists",
        )


class RoleNotFoundException(ParallelException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ROLE_002",
            message="Role not found",
        )
