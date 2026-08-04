from fastapi import status

from app.exceptions.exceptions import ParallelException


class RolePermissionAlreadyExistsException(
    ParallelException,
):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="ROLE_PERMISSION_001",
            message="Permission already assigned to role",
        )


class RolePermissionNotFoundException(
    ParallelException,
):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="ROLE_PERMISSION_002",
            message="Permission assignment not found",
        )
