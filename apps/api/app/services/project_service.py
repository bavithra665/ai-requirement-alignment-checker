from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.project_repository import project_repo
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.models.project import Project

class ProjectService:
    async def create_project(self, db: AsyncSession, project_in: ProjectCreate, current_user_id: UUID) -> Project:
        # Override owner_id to be the current user
        project_in.owner_id = current_user_id
        return await project_repo.create(db=db, obj_in=project_in, created_by_id=current_user_id)

    async def get_project(self, db: AsyncSession, project_id: UUID) -> Optional[Project]:
        return await project_repo.get(db=db, id=project_id)

    async def get_projects(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Project]:
        return await project_repo.get_multi(db=db, skip=skip, limit=limit)

    async def update_project(
        self, db: AsyncSession, project_id: UUID, project_in: ProjectUpdate, current_user_id: UUID
    ) -> Optional[Project]:
        project = await project_repo.get(db=db, id=project_id)
        if not project:
            return None
        return await project_repo.update(db=db, db_obj=project, obj_in=project_in, updated_by_id=current_user_id)

    async def delete_project(self, db: AsyncSession, project_id: UUID, current_user_id: UUID) -> Optional[Project]:
        return await project_repo.remove(db=db, id=project_id, updated_by_id=current_user_id)

project_service = ProjectService()
