from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    # Create User
    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    #Get by ID
    def get_by_id(self, user_id: UUID) -> User | None:
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    #Get by Email
    def get_by_email(self, email: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    #Update
    def update(self) -> None:
        self.db.commit()

    #Delete
    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()