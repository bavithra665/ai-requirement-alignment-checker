from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.jira_service import jira_service
from app.schemas.jira_story import JiraStoryResponse
from app.repositories.project_repository import project_repo

router = APIRouter()


@router.get("/status")
async def jira_status():
    """
    Returns Jira connection status and setup instructions if unconfigured.
    Never raises — always returns a structured response.
    """
    return jira_service.get_status()


@router.post("/projects/{project_id}/sync", status_code=status.HTTP_200_OK)
async def sync_jira_stories(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Trigger a full sync of Jira stories for the given project.
    The project must have a jira_project_key set.
    """
    if not jira_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Jira is not configured. Add JIRA_BASE_URL, JIRA_API_TOKEN, JIRA_USER_EMAIL to .env",
        )

    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.jira_project_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This project does not have a Jira Project Key configured.",
        )

    try:
        result = await jira_service.sync_project_stories(
            db=db,
            project_id=project_id,
            jira_project_key=project.jira_project_key,
            current_user_id=current_user.id,
        )
        return {"message": "Sync completed successfully", **result}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Jira sync failed: {str(exc)}")


@router.get("/projects/{project_id}/stories", response_model=List[JiraStoryResponse])
async def list_jira_stories(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    List all stored Jira stories for a project (from DB — no live Jira call).
    """
    return await jira_service.get_project_stories(db=db, project_id=project_id)
