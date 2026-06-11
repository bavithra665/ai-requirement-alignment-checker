from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema

class MismatchReportBase(BaseModel):
    project_id: UUID
    alignment_result_id: UUID
    mismatch_type: str
    description: str
    suggested_fix: Optional[str] = None
    status: str = "Open"
    severity: str = "Medium"

class MismatchReportCreate(MismatchReportBase):
    pass

class MismatchReportUpdate(BaseModel):
    mismatch_type: Optional[str] = None
    description: Optional[str] = None
    suggested_fix: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    resolution_notes: Optional[str] = None
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None

class MismatchReportResponse(MismatchReportBase, BaseDomainSchema):
    reviewed_by_id: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
