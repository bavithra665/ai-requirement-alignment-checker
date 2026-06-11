from typing import Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema


class CodeArtifactBase(BaseModel):
    pull_request_id: UUID
    artifact_type: str           # "Function", "Class", "API Endpoint"
    artifact_name: str           # e.g. "edit_invoice", "/invoice/edit"
    file_path: str               # e.g. "app/routes/invoice.py"
    artifact_metadata: Optional[Dict[str, Any]] = None  # line_number, http_method, args, decorators, etc.


class CodeArtifactCreate(CodeArtifactBase):
    pass


class CodeArtifactUpdate(BaseModel):
    artifact_name: Optional[str] = None
    file_path: Optional[str] = None
    artifact_metadata: Optional[Dict[str, Any]] = None


class CodeArtifactResponse(CodeArtifactBase, BaseDomainSchema):
    pass
