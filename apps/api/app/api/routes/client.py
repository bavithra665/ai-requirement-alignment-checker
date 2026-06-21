from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.api.deps import get_current_user, require_role, get_db
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.requirement import Requirement
from app.models.requirement_version import RequirementVersion
from app.models.client_approval import ClientApproval
from app.models.notification import Notification, NotificationType
from app.schemas.project import ProjectResponse
from app.schemas.requirement_version import RequirementVersionResponse
from app.repositories.requirement_repository import requirement_repo
from app.repositories.requirement_version_repository import requirement_version_repo
from app.repositories.client_approval_repository import client_approval_repo
from app.repositories.notification_repository import notification_repo
from app.schemas.notification import NotificationCreate

router = APIRouter()


class ApprovalAction(BaseModel):
    comment: Optional[str] = None


@router.get("/projects", response_model=List[ProjectResponse], dependencies=[Depends(require_role(UserRole.CLIENT))])
async def get_client_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all projects where project.client_name matches current user's company_name.
    Only accessible by CLIENT role users.
    """
    if not current_user.company_name:
        return []

    stmt = select(Project).where(
        Project.client_name == current_user.company_name,
        Project.is_deleted == False
    )
    result = await db.execute(stmt)
    projects = list(result.scalars().all())
    return projects


@router.get("/projects/{project_id}/requirement-versions", response_model=List[RequirementVersionResponse], dependencies=[Depends(require_role(UserRole.CLIENT))])
async def get_project_requirement_versions(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all requirement versions for a project.
    Client must have access to the project (company_name match).
    """
    # Verify project belongs to client's company
    stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.client_name != current_user.company_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project"
        )

    # Get all requirements for this project
    all_reqs = await requirement_repo.get_multi(db=db, limit=1000)
    proj_reqs = [r for r in all_reqs if r.project_id == project_id]
    proj_req_ids = [r.id for r in proj_reqs]

    # Get all versions for these requirements
    all_versions = await requirement_version_repo.get_multi(db=db, limit=5000)
    relevant_versions = [v for v in all_versions if v.requirement_id in proj_req_ids]

    return relevant_versions


@router.post("/projects/{project_id}/requirement-versions/{version_id}/approve", response_model=RequirementVersionResponse, dependencies=[Depends(require_role(UserRole.CLIENT))])
async def approve_requirement_version(
    project_id: UUID,
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Client approves a requirement version.
    Creates an approved ClientApproval record and notification for developer.
    """
    # Get requirement version
    version = await requirement_version_repo.get(db=db, id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Requirement version not found")

    # Get requirement to verify it belongs to the project
    requirement = await requirement_repo.get(db=db, id=version.requirement_id)
    if not requirement or requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found in this project")

    # Get project to verify client access
    stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project or project.client_name != current_user.company_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project"
        )

    # Create or update ClientApproval
    stmt = select(ClientApproval).where(ClientApproval.requirement_version_id == version_id)
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()

    if not approval:
        approval = ClientApproval(
            requirement_version_id=version_id,
            status="approved",
            comments="Approved by client",
            created_by_id=current_user.id,
            updated_by_id=current_user.id
        )
    else:
        approval.status = "approved"
        approval.updated_by_id = current_user.id

    db.add(approval)
    await db.flush()

    # Create notification for developer
    notification_data = NotificationCreate(
        developer_id=project.owner_id,
        project_id=project_id,
        requirement_version_id=version_id,
        notification_type=NotificationType.CLIENT_APPROVED,
        message=f"Client {current_user.full_name} approved {requirement.title}"
    )
    await notification_repo.create(db=db, obj_in=notification_data)

    await db.commit()
    await db.refresh(version)
    return version


@router.post("/projects/{project_id}/requirement-versions/{version_id}/reject", response_model=RequirementVersionResponse, dependencies=[Depends(require_role(UserRole.CLIENT))])
async def reject_requirement_version(
    project_id: UUID,
    version_id: UUID,
    action_in: ApprovalAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Client rejects a requirement version with a comment.
    Creates a rejected ClientApproval record and notification for developer.
    """
    # Get requirement version
    version = await requirement_version_repo.get(db=db, id=version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Requirement version not found")

    # Get requirement to verify it belongs to the project
    requirement = await requirement_repo.get(db=db, id=version.requirement_id)
    if not requirement or requirement.project_id != project_id:
        raise HTTPException(status_code=404, detail="Requirement not found in this project")

    # Get project to verify client access
    stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()

    if not project or project.client_name != current_user.company_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project"
        )

    # Create or update ClientApproval
    stmt = select(ClientApproval).where(ClientApproval.requirement_version_id == version_id)
    result = await db.execute(stmt)
    approval = result.scalar_one_or_none()

    comment_text = action_in.comment or "Client requested changes"
    if not approval:
        approval = ClientApproval(
            requirement_version_id=version_id,
            status="requested_changes",
            comments=comment_text,
            created_by_id=current_user.id,
            updated_by_id=current_user.id
        )
    else:
        approval.status = "requested_changes"
        approval.comments = comment_text
        approval.updated_by_id = current_user.id

    db.add(approval)
    await db.flush()

    # Create notification for developer
    notification_data = NotificationCreate(
        developer_id=project.owner_id,
        project_id=project_id,
        requirement_version_id=version_id,
        notification_type=NotificationType.CLIENT_REQUESTED_CHANGES,
        message=f"Client {current_user.full_name} requested changes on {requirement.title}: {comment_text}"
    )
    await notification_repo.create(db=db, obj_in=notification_data)

    await db.commit()
    await db.refresh(version)
    return version
