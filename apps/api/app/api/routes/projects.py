from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import project_service

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    return await project_service.create_project(db=db, project_in=project_in, current_user_id=current_user.id)

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    # In a real app we might filter by user, but for now we list all
    return await project_service.get_projects(db=db, skip=skip, limit=limit)

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    project = await project_service.get_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_in: ProjectUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    project = await project_service.update_project(db=db, project_id=project_id, project_in=project_in, current_user_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}", response_model=ProjectResponse)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    project = await project_service.delete_project(db=db, project_id=project_id, current_user_id=current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
