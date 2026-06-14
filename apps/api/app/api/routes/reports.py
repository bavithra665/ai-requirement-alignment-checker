from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.services.reporting_service import reporting_service
from app.schemas.mismatch_report import (
    MismatchReportResponse,
    MismatchReportUpdate
)
from app.repositories.mismatch_report_repository import mismatch_report_repo
from app.repositories.project_repository import project_repo

router = APIRouter()

@router.post("/mismatches/generate/{project_id}", response_model=List[MismatchReportResponse])
async def generate_mismatch_reports(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """Generate mismatch reports from alignment results for a project."""
    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        reports = await reporting_service.generate_mismatch_reports(
            db=db, project_id=project_id, current_user_id=current_user.id
        )
        return reports
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/mismatches/{project_id}", response_model=List[MismatchReportResponse])
async def get_mismatch_reports(
    project_id: UUID,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """Get all mismatch reports for a project with optional filters."""
    from sqlalchemy.future import select
    from app.models.mismatch_report import MismatchReport

    stmt = select(MismatchReport).where(
        MismatchReport.project_id == project_id,
        MismatchReport.is_deleted == False
    )

    if status and status != "All":
        stmt = stmt.where(MismatchReport.status == status)
    if severity and severity != "All":
        stmt = stmt.where(MismatchReport.severity == severity)

    stmt = stmt.order_by(MismatchReport.created_at.desc())

    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.patch("/mismatches/{mismatch_id}", response_model=MismatchReportResponse)
async def update_mismatch_report(
    mismatch_id: UUID,
    report_in: MismatchReportUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """Update a mismatch report's status or resolution notes."""
    report = await mismatch_report_repo.get(db=db, id=mismatch_id)
    if not report:
        raise HTTPException(status_code=404, detail="Mismatch report not found")

    from datetime import datetime, timezone
    
    update_data = report_in.dict(exclude_unset=True)
    
    if "status" in update_data and update_data["status"] in ["Reviewed", "Resolved"]:
        update_data["reviewed_by_id"] = current_user.id
        update_data["reviewed_at"] = datetime.now(timezone.utc)

    report = await mismatch_report_repo.update(db=db, db_obj=report, obj_in=update_data)
    return report

@router.get("/health/{project_id}")
async def get_project_health(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """Get overall project health score and metrics."""
    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        health = await reporting_service.get_project_health(db=db, project_id=project_id)
        return health
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/executive/{project_id}")
async def get_executive_report(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """Generate executive summary report with Groq narrative."""
    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        report = await reporting_service.generate_executive_report(db=db, project_id=project_id)
        return report
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/export/mismatches/{project_id}")
async def export_mismatches_csv(
    project_id: UUID,
    format: str = Query("csv", description="Export format"),
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """Export mismatch reports as CSV."""
    if format != "csv":
        raise HTTPException(status_code=400, detail="Only CSV export is supported")
        
    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    import io
    import csv
    from sqlalchemy.future import select
    from app.models.mismatch_report import MismatchReport

    stmt = select(MismatchReport).where(
        MismatchReport.project_id == project_id,
        MismatchReport.is_deleted == False
    ).order_by(MismatchReport.created_at.desc())

    result = await db.execute(stmt)
    reports = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Type", "Severity", "Status", "Description", 
        "Suggested Fix", "Resolution Notes", "Created At"
    ])
    
    for r in reports:
        writer.writerow([
            str(r.id), r.mismatch_type, r.severity, r.status,
            r.description, r.suggested_fix or "", 
            r.resolution_notes or "", 
            r.created_at.isoformat() if r.created_at else ""
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=mismatches_{project_id}.csv"}
    )

@router.get("/export/executive/{project_id}")
async def export_executive_csv(
    project_id: UUID,
    format: str = Query("csv", description="Export format"),
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """Export executive summary as CSV."""
    if format != "csv":
        raise HTTPException(status_code=400, detail="Only CSV export is supported")
        
    project = await project_repo.get(db=db, id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        report = await reporting_service.generate_executive_report(db=db, project_id=project_id)
        
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Section", "Metric/Item", "Value"])
        
        # Summary
        writer.writerow(["Project Summary", "Name", report["project_summary"]["name"]])
        writer.writerow(["Project Summary", "Client", report["project_summary"]["client_name"]])
        writer.writerow(["Project Summary", "Status", report["project_summary"]["status"]])
        
        # Health
        writer.writerow(["Project Health", "Score", str(report["health"]["health_score"])])
        writer.writerow(["Project Health", "Status", report["health"]["health_status"]])
        writer.writerow(["Project Health", "Drift %", str(report["health"]["drift_percentage"])])
        
        # Top Risks
        for i, risk in enumerate(report["top_risks"]):
            writer.writerow([f"Top Risk #{i+1}", risk["mismatch_type"], f"{risk['severity']} - {risk['description']}"])
            
        # Narrative
        writer.writerow(["Narrative Summary", "AI Explanation", report["narrative"]])
        writer.writerow(["Recommendations", "Action Items", report["recommendations"]])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=executive_summary_{project_id}.csv"}
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
