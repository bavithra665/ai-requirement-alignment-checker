from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.requirement_version_repository import requirement_version_repo
from app.schemas.requirement_version import RequirementVersionCreate, RequirementVersionUpdate
from app.models.requirement_version import RequirementVersion

class VersioningService:
    async def create_initial_version(self, db: AsyncSession, requirement_id: UUID, content: str, ai_summary: str, current_user_id: UUID) -> RequirementVersion:
        version_in = RequirementVersionCreate(
            requirement_id=requirement_id,
            version_number=1,
            content=content,
            ai_summary=ai_summary,
            status="Pending Review",
            is_baseline=False
        )
        return await requirement_version_repo.create(db=db, obj_in=version_in, created_by_id=current_user_id)

    async def review_version(self, db: AsyncSession, version_id: UUID, action: str, current_user_id: UUID) -> Optional[RequirementVersion]:
        version = await requirement_version_repo.get(db=db, id=version_id)
        if not version:
            return None
            
        if action == "approve":
            new_status = "Approved"
            is_baseline = True
        elif action == "request_changes":
            new_status = "Changes Requested"
            is_baseline = False
        else:
            return None

        update_in = RequirementVersionUpdate(status=new_status, is_baseline=is_baseline)
        return await requirement_version_repo.update(db=db, db_obj=version, obj_in=update_in, updated_by_id=current_user_id)

    async def create_new_version(self, db: AsyncSession, requirement_id: UUID, new_content: str, change_summary: str, ai_summary: str, current_user_id: UUID) -> RequirementVersion:
        # Get all versions to determine the next version number
        versions = await requirement_version_repo.get_multi(db=db, limit=1000)
        req_versions = [v for v in versions if v.requirement_id == requirement_id]
        latest_num = max([v.version_number for v in req_versions]) if req_versions else 0
        
        version_in = RequirementVersionCreate(
            requirement_id=requirement_id,
            version_number=latest_num + 1,
            content=new_content,
            change_summary=change_summary,
            ai_summary=ai_summary,
            status="Pending Review",
            is_baseline=False
        )
        return await requirement_version_repo.create(db=db, obj_in=version_in, created_by_id=current_user_id)

versioning_service = VersioningService()
