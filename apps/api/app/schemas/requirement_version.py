from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema

class RequirementVersionBase(BaseModel):
    requirement_id: UUID
    version_number: int
    content: str
    change_summary: Optional[str] = None
    ai_summary: Optional[str] = None
    status: str = "Draft"
    is_baseline: bool = False

class RequirementVersionCreate(RequirementVersionBase):
    pass

class RequirementVersionUpdate(BaseModel):
    content: Optional[str] = None
    change_summary: Optional[str] = None
    ai_summary: Optional[str] = None
    status: Optional[str] = None
    is_baseline: Optional[bool] = None

class RequirementVersionResponse(RequirementVersionBase, BaseDomainSchema):
    pass
