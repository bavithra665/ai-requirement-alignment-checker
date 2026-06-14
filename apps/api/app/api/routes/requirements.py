from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from pydantic import BaseModel
from app.services.versioning_service import versioning_service
from app.repositories.requirement_version_repository import requirement_version_repo
from app.repositories.requirement_repository import requirement_repo
from app.schemas.requirement_version import RequirementVersionResponse

router = APIRouter()

class ReviewRequest(BaseModel):
    action: str  # "approve" or "request_changes"
    comment: Optional[str] = None

@router.get("/project/{project_id}", response_model=List[RequirementVersionResponse])
async def get_project_requirements(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    Returns the latest versions of all requirements for a specific project.
    """
    all_reqs = await requirement_repo.get_multi(db=db, limit=1000)
    proj_reqs = [r for r in all_reqs if r.project_id == project_id]
    proj_req_ids = [r.id for r in proj_reqs]

    all_versions = await requirement_version_repo.get_multi(db=db, limit=5000)
    
    # Filter to only the versions belonging to this project's requirements
    relevant_versions = [v for v in all_versions if v.requirement_id in proj_req_ids]
    
    # We might want all history or just latest. For now return all history.
    return relevant_versions

@router.post("/{version_id}/review", response_model=RequirementVersionResponse)
async def review_requirement_version(
    version_id: UUID,
    payload: ReviewRequest,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """
    Allows a client to approve or request changes to a specific requirement version.
    """
    if payload.action not in ["approve", "request_changes"]:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'request_changes'.")

    # In a real app we'd save the comment to the ClientApproval table.
    # For now, the VersioningService updates the state.
    updated_version = await versioning_service.review_version(
        db=db, 
        version_id=version_id, 
        action=payload.action, 
        current_user_id=current_user.id
    )
    
    if not updated_version:
        raise HTTPException(status_code=404, detail="Requirement Version not found")
        
    return updated_version
