from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema

class RequirementBase(BaseModel):
    project_id: UUID
    title: str
    description: Optional[str] = None

class RequirementCreate(RequirementBase):
    pass

class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class RequirementResponse(RequirementBase, BaseDomainSchema):
    pass
