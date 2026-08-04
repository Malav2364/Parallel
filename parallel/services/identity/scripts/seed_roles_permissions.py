from app.core.config import settings
from app.core.database import SessionLocal
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User

ROLES = [
    {
        "name": "Admin",
        "description": "System Administrator",
    },
    {
        "name": "Manager",
        "description": "Manager",
    },
    {
        "name": "User",
        "description": "Regular User",
    },
]

PERMISSIONS = [
    {
        "name": "manage_users",
        "description": "Manage users",
    },
    {
        "name": "manage_roles",
        "description": "Manage roles",
    },
    {
        "name": "manage_permissions",
        "description": "Manage permissions",
    },
    {
        "name": "view_profile",
        "description": "View own profile",
    },
    {
        "name": "edit_profile",
        "description": "Edit own profile",
    },
]

ROLE_PERMISSIONS = {
    "Admin": [
        "manage_users",
        "manage_roles",
        "manage_permissions",
        "view_profile",
        "edit_profile",
    ],
    "Manager": [
        "manage_users",
        "view_profile",
        "edit_profile",
    ],
    "User": [
        "view_profile",
        "edit_profile",
    ],
}


def seed_roles(db):
    for role_data in ROLES:
        role = db.query(Role).filter(Role.name == role_data["name"]).first()

        if role is None:
            role = Role(**role_data)
            db.add(role)

    db.commit()


def seed_permissions(db):
    for permission_data in PERMISSIONS:
        permission = (
            db.query(Permission)
            .filter(Permission.name == permission_data["name"])
            .first()
        )

        if permission is None:
            permission = Permission(**permission_data)
            db.add(permission)

    db.commit()


def seed_role_permissions(db):
    for role_name, permission_names in ROLE_PERMISSIONS.items():
        role = db.query(Role).filter(Role.name == role_name).first()

        for permission_name in permission_names:
            permission = (
                db.query(Permission).filter(Permission.name == permission_name).first()
            )

            exists = (
                db.query(RolePermission)
                .filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
                .first()
            )

            if exists is None:
                db.add(
                    RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                )

    db.commit()


def assign_admin_role(
    db,
    admin_email: str,
):
    user = db.query(User).filter(User.email == admin_email).first()

    if user is None:
        print(f"User '{admin_email}' not found.")
        return

    admin_role = db.query(Role).filter(Role.name == "Admin").first()

    user.role_id = admin_role.id

    db.commit()

    print(f"Admin role assigned to {admin_email}")


def main():
    db = SessionLocal()

    try:
        assign_admin_role(
            db,
            settings.ADMIN_EMAIL,
        )
        seed_roles(db)
        print("Roles seeded")

        seed_permissions(db)
        print("Permissions seeded")

        seed_role_permissions(db)
        print("Role permissions assigned")

        print("\nIdentity RBAC seeding completed successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
