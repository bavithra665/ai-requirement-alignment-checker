from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema

class ClientApprovalBase(BaseModel):
    requirement_version_id: UUID
    status: str
    comments: Optional[str] = None

class ClientApprovalCreate(ClientApprovalBase):
    pass

class ClientApprovalUpdate(BaseModel):
    status: Optional[str] = None
    comments: Optional[str] = None

class ClientApprovalResponse(ClientApprovalBase, BaseDomainSchema):
    pass
