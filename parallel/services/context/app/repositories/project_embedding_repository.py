from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProjectEmbeddingEntity


class ProjectEmbeddingRepository:
    """Persistence for the Tier-2 project-embedding cache."""

    def __init__(self, db: Session):
        self.db = db

    def get_many(self, user_id: str) -> dict[str, tuple[str, list[float]]]:
        """Return ``{project_id: (text_hash, embedding)}`` for one user."""

        statement = select(ProjectEmbeddingEntity).where(
            ProjectEmbeddingEntity.user_id == user_id,
        )
        rows = self.db.scalars(statement).all()
        return {row.project_id: (row.text_hash, row.embedding) for row in rows}

    def upsert(
        self,
        user_id: str,
        project_id: str,
        text_hash: str,
        embedding: list[float],
    ) -> None:
        """Insert or refresh one project's cached embedding (no commit)."""

        statement = select(ProjectEmbeddingEntity).where(
            ProjectEmbeddingEntity.user_id == user_id,
            ProjectEmbeddingEntity.project_id == project_id,
        )
        row = self.db.scalar(statement)

        if row is None:
            self.db.add(
                ProjectEmbeddingEntity(
                    user_id=user_id,
                    project_id=project_id,
                    text_hash=text_hash,
                    embedding=embedding,
                )
            )
        else:
            row.text_hash = text_hash
            row.embedding = embedding

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
