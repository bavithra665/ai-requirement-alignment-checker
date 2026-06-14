from typing import Any
from uuid import UUID
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.services.storage_service import storage_service
from app.services.extraction_service import extraction_service
from app.services.ai_service import ai_service
from app.services.versioning_service import versioning_service
from app.repositories.requirement_repository import requirement_repo
from app.schemas.requirement import RequirementCreate
from pydantic import BaseModel

router = APIRouter()

class UploadResponse(BaseModel):
    message: str
    requirements_extracted: int

@router.post("/{project_id}/upload-brd", response_model=UploadResponse)
async def upload_brd(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    # 1. Save file locally
    file_path = await storage_service.save_brd(project_id=project_id, version=1, file=file)

    # 2. Extract deterministic requirements
    if file.filename.endswith('.pdf'):
        extracted_texts = extraction_service.parse_pdf(file_path)
    else:
        extracted_texts = extraction_service.parse_docx(file_path)

    if not extracted_texts:
        raise HTTPException(status_code=400, detail="No extractable requirements found in document.")

    # 3. For each extracted text block, create a Requirement and an initial Version
    created_count = 0
    for text_block in extracted_texts:
        # Create base Requirement
        req_in = RequirementCreate(project_id=project_id, title=text_block[:50] + "...")
        req = await requirement_repo.create(db=db, obj_in=req_in, created_by_id=current_user.id)
        
        # 4. Use AI to generate summary (Optional, but part of requirement)
        # We pass it as a list of 1 to get a summary for this specific block, or we could summarize the whole document.
        # The spec says "AI Summary Generation... Generate Business Summary, Key Features... Store generated summaries"
        # Since it takes time, we should ideally do this asynchronously, but for MVP we will await it.
        ai_summary = await ai_service.generate_summary([text_block])
        
        # Create initial RequirementVersion
        await versioning_service.create_initial_version(
            db=db,
            requirement_id=req.id,
            content=text_block,
            ai_summary=ai_summary,
            current_user_id=current_user.id
        )
        created_count += 1

    return UploadResponse(message="BRD uploaded and parsed successfully.", requirements_extracted=created_count)
