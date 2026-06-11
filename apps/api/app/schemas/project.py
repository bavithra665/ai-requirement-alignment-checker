from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema

class ProjectBase(BaseModel):
    name: str
    client_name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    jira_project_key: Optional[str] = None
    status: str = "Draft"
    owner_id: UUID

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client_name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    jira_project_key: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[UUID] = None

class ProjectResponse(ProjectBase, BaseDomainSchema):
    pass
