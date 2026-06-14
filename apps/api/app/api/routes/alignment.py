from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.alignment_engine import alignment_engine
from app.schemas.alignment_result import AlignmentResultResponse
from app.repositories.alignment_result_repository import alignment_result_repo
from app.repositories.project_repository import project_repo

router = APIRouter()


@router.post("/run/{project_id}", status_code=status.HTTP_202_ACCEPTED)
async def run_alignment(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Trigger the AI Alignment Engine for a project.
    Indexes all artifacts into ChromaDB, runs relationship-aware similarity scoring
    (Requirement → Jira → PR → Code Artifact), generates Groq explanations,
    and persists AlignmentResult records.
    """
    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        results = await alignment_engine.run_alignment(
            db=db,
            project_id=project_id,
            current_user_id=current_user.id,
        )
        return {
            "message": "Alignment analysis completed successfully",
            "project_id": str(project_id),
            "results_generated": len(results),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Alignment engine failed: {str(exc)}"
        )


@router.post("/index/{project_id}", status_code=status.HTTP_200_OK)
async def index_project_artifacts(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Index all project artifacts into ChromaDB without running scoring.
    Call this endpoint after: BRD approval, Jira sync, PR sync, or code extraction.
    Vectors are stored and reused in subsequent alignment runs.
    """
    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        counts = await alignment_engine.index_project(db=db, project_id=project_id)
        return {
            "message": "Project artifacts indexed successfully",
            "project_id": str(project_id),
            "indexed": counts,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(exc)}"
        )


@router.get("/results/{project_id}", response_model=List[AlignmentResultResponse])
async def get_alignment_results(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Retrieve all alignment results for a project ordered by overall score ascending
    (lowest alignment first for risk-first prioritization).
    """
    from sqlalchemy.future import select
    from app.models.alignment_result import AlignmentResult

    stmt = (
        select(AlignmentResult)
        .where(
            AlignmentResult.project_id == project_id,
            AlignmentResult.is_deleted == False,
        )
        .order_by(AlignmentResult.overall_alignment_score.asc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/result/{result_id}", response_model=AlignmentResultResponse)
async def get_alignment_result_detail(
    result_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
):
    """
    Retrieve the full detail of a single alignment result record
    including all relationship scores and the Groq explanation.
    """
    record = await alignment_result_repo.get(db=db, id=result_id)
    if not record:
        raise HTTPException(status_code=404, detail="Alignment result not found")
    return record
