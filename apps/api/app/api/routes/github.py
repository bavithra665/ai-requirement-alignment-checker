from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.github_service import github_service
from app.services.code_extraction_service import code_extraction_service
from app.schemas.pull_request import PullRequestResponse
from app.schemas.code_artifact import CodeArtifactResponse
from app.repositories.project_repository import project_repo
from app.repositories.pull_request_repository import pull_request_repo
from app.repositories.code_artifact_repository import code_artifact_repo

router = APIRouter()


@router.get("/status")
async def github_status():
    """
    Returns GitHub connection status and setup instructions if unconfigured.
    Never raises — always returns a structured response.
    """
    return github_service.get_status()


@router.post("/projects/{project_id}/sync-prs", status_code=status.HTTP_200_OK)
async def sync_pull_requests(
    project_id: UUID,
    state: str = "all",
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Sync Pull Requests from the project's repository URL.
    The project must have a repository_url configured.
    Query param `state`: "open" | "closed" | "all" (default: all)
    """
    if not github_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub is not configured. Add GITHUB_TOKEN to .env",
        )

    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.repository_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This project does not have a Repository URL configured.",
        )

    if state not in ("open", "closed", "all"):
        raise HTTPException(status_code=400, detail="state must be 'open', 'closed', or 'all'")

    try:
        result = await github_service.sync_pull_requests(
            db=db,
            project_id=project_id,
            repository_url=project.repository_url,
            current_user_id=current_user.id,
            state=state,
        )
        return {"message": "PR sync completed successfully", **result}
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"GitHub sync failed: {str(exc)}")


@router.get("/projects/{project_id}/prs", response_model=List[PullRequestResponse])
async def list_pull_requests(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    List all stored Pull Requests for a project (from DB).
    """
    return await github_service.get_project_prs(db=db, project_id=project_id)


@router.post("/prs/{pr_id}/extract-symbols", status_code=status.HTTP_200_OK)
async def extract_pr_symbols(
    pr_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Run code symbol extraction (Python AST) on all changed files in a PR.
    Requires GitHub token to fetch file contents.
    Previous extraction results are replaced (idempotent).
    """
    if not github_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub token not configured — cannot fetch file contents.",
        )

    pr = await pull_request_repo.get(db=db, id=pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull Request not found")

    changed_files = pr.changed_files or []
    if not changed_files:
        return {"message": "No changed files found on this PR. Run PR sync first.", "processed_files": 0}

    try:
        result = await code_extraction_service.process_pr_files(
            db=db,
            pull_request_id=pr.id,
            repository_url=pr.repository_url,
            changed_files=changed_files,
            head_sha=pr.head_sha,
            current_user_id=current_user.id,
        )
        return {"message": "Extraction completed", **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(exc)}")


@router.get("/prs/{pr_id}/symbols", response_model=List[CodeArtifactResponse])
async def get_pr_symbols(
    pr_id: UUID,
    artifact_type: str = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Get extracted code symbols for a PR from DB.
    Optional ?artifact_type=Function|Class|API+Endpoint filter.
    """
    from app.models.code_artifact import ArtifactType
    
    pr = await pull_request_repo.get(db=db, id=pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull Request not found")

    if artifact_type:
        try:
            atype = ArtifactType(artifact_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid artifact_type. Must be one of: {[t.value for t in ArtifactType]}"
            )
        return await code_artifact_repo.get_by_pull_request_and_type(
            db=db, pull_request_id=pr_id, artifact_type=atype
        )
    
    return await code_artifact_repo.get_by_pull_request(db=db, pull_request_id=pr_id)
