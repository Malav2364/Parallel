from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register_user(self, user: UserCreate) -> User:

        existing_user = self.repository.get_by_email(user.email)

        if existing_user:
            raise ValueError("Email already registered")

        hashed_password = hash_password(user.password)

        new_user = User(
            email=user.email,
            password_hash=hashed_password,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        return self.repository.create(new_user)