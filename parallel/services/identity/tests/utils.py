from app.core.jwt import create_email_verification_token
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import User
from tests.database import TestingSessionLocal
from tests.factories import USER_DATA


def register_and_verify_user(client):
    client.post(
        "/api/v1/auth/register",
        json=USER_DATA,
    )

    token = create_email_verification_token(
        {
            "sub": USER_DATA["email"],
        }
    )

    client.get(
        "/api/v1/auth/verify-email",
        params={
            "token": token,
        },
    )


def login_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": USER_DATA["email"],
            "password": USER_DATA["password"],
        },
    )

    return response.json()


def assign_permission_to_user(
    email: str,
    permission_name: str,
):
    db = TestingSessionLocal()

    user = db.query(User).filter(User.email == email).first()

    role = db.query(Role).filter(Role.name == "Admin").first()

    if role is None:
        role = Role(
            name="Admin",
            description="Administrator",
        )
        db.add(role)
        db.commit()
        db.refresh(role)

    permission = db.query(Permission).filter(Permission.name == permission_name).first()

    if permission is None:
        permission = Permission(
            name=permission_name,
            description=permission_name,
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)

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

    user.role_id = role.id

    db.commit()
    db.close()
