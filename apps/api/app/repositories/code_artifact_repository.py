from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.base import BaseRepository
from app.models.code_artifact import CodeArtifact, ArtifactType
from app.schemas.code_artifact import CodeArtifactCreate, CodeArtifactUpdate


class CodeArtifactRepository(BaseRepository[CodeArtifact, CodeArtifactCreate, CodeArtifactUpdate]):

    async def get_by_pull_request(
        self, db: AsyncSession, *, pull_request_id: UUID
    ) -> List[CodeArtifact]:
        stmt = select(self.model).where(
            self.model.pull_request_id == pull_request_id,
            self.model.is_deleted == False,
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_pull_request_and_type(
        self, db: AsyncSession, *, pull_request_id: UUID, artifact_type: ArtifactType
    ) -> List[CodeArtifact]:
        stmt = select(self.model).where(
            self.model.pull_request_id == pull_request_id,
            self.model.artifact_type == artifact_type,
            self.model.is_deleted == False,
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_pull_request(
        self, db: AsyncSession, *, pull_request_id: UUID
    ) -> None:
        """Hard-delete all artifacts for a PR before re-extracting (idempotent re-sync)."""
        from sqlalchemy import delete
        stmt = delete(self.model).where(self.model.pull_request_id == pull_request_id)
        await db.execute(stmt)
        await db.commit()


code_artifact_repo = CodeArtifactRepository(CodeArtifact)
