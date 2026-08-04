from app.core.logger import logger
from app.exceptions.permission import (
    PermissionNotFoundException,
)
from app.exceptions.role import (
    RoleAlreadyExistsException,
    RoleNotFoundException,
)
from app.exceptions.role_permission import (
    RolePermissionAlreadyExistsException,
    RolePermissionNotFoundException,
)
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_permission_repository import (
    RolePermissionRepository,
)
from app.repositories.role_repository import RoleRepository


class RoleService:
    def __init__(
        self,
        repository: RoleRepository,
        permission_repository: PermissionRepository,
        role_permission_repository: RolePermissionRepository,
    ):
        self.repository = repository
        self.permission_repository = permission_repository
        self.role_permission_repository = role_permission_repository

    def create_role(
        self,
        name: str,
        description: str | None = None,
    ) -> Role:

        existing_role = self.repository.get_by_name(
            name,
        )

        if existing_role:
            raise RoleAlreadyExistsException()

        role = Role(
            name=name,
            description=description,
        )

        created_role = self.repository.create(
            role,
        )

        logger.info(
            "Role created: %s",
            created_role.name,
        )

        return created_role

    def get_role(
        self,
        role_id: str,
    ) -> Role:

        role = self.repository.get_by_id(
            role_id,
        )

        if role is None:
            raise RoleNotFoundException()

        return role

    def get_roles(
        self,
    ) -> list[Role]:

        return self.repository.get_all()

    def update_role(
        self,
        role_id: str,
        name: str,
        description: str | None = None,
    ) -> Role:

        role = self.repository.get_by_id(
            role_id,
        )

        if role is None:
            raise RoleNotFoundException()

        existing_role = self.repository.get_by_name(
            name,
        )

        if existing_role and existing_role.id != role.id:
            raise RoleAlreadyExistsException()

        role.name = name
        role.description = description

        updated_role = self.repository.update(
            role,
        )

        logger.info(
            "Role updated: %s",
            updated_role.name,
        )

        return updated_role

    def delete_role(
        self,
        role_id: str,
    ) -> None:

        role = self.repository.get_by_id(
            role_id,
        )

        if role is None:
            raise RoleNotFoundException()

        self.repository.delete(
            role,
        )

        logger.info(
            "Role deleted: %s",
            role.name,
        )

    def assign_permission(
        self,
        role_id: str,
        permission_id: str,
    ) -> None:

        role = self.repository.get_by_id(role_id)

        if role is None:
            raise RoleNotFoundException()

        permission = self.permission_repository.get_by_id(
            permission_id,
        )

        if permission is None:
            raise PermissionNotFoundException()

        existing = self.role_permission_repository.get(
            role_id,
            permission_id,
        )

        if existing:
            raise RolePermissionAlreadyExistsException()

        assignment = RolePermission(
            role_id=role_id,
            permission_id=permission_id,
        )

        self.role_permission_repository.create(
            assignment,
        )

        logger.info(
            "Permission %s assigned to role %s",
            permission.name,
            role.name,
        )

    def remove_permission(
        self,
        role_id: str,
        permission_id: str,
    ) -> None:

        assignment = self.role_permission_repository.get(
            role_id,
            permission_id,
        )

        if assignment is None:
            raise RolePermissionNotFoundException()

        self.role_permission_repository.delete(
            assignment,
        )

        logger.info(
            "Permission removed from role",
        )

    def get_permissions(
        self,
        role_id: str,
    ):

        role = self.repository.get_with_permissions(
            role_id,
        )

        if role is None:
            raise RoleNotFoundException()

        return [rp.permission for rp in role.permissions]
