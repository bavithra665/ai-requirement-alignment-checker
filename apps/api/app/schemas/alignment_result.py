from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema

class AlignmentResultBase(BaseModel):
    project_id: UUID
    requirement_version_id: UUID
    jira_story_id: Optional[UUID] = None
    pull_request_id: Optional[UUID] = None
    code_artifact_id: Optional[UUID] = None
    
    requirement_jira_score: Optional[int] = None
    jira_pr_score: Optional[int] = None
    pr_artifact_score: Optional[int] = None
    overall_alignment_score: int
    
    alignment_status: str  # Aligned, Potential Drift, Misaligned
    confidence: int       # 0-100
    explanation: Optional[str] = None
    
    # Compatibility
    score: int
    summary: Optional[str] = None

class AlignmentResultCreate(AlignmentResultBase):
    pass

class AlignmentResultUpdate(BaseModel):
    requirement_jira_score: Optional[int] = None
    jira_pr_score: Optional[int] = None
    pr_artifact_score: Optional[int] = None
    overall_alignment_score: Optional[int] = None
    alignment_status: Optional[str] = None
    confidence: Optional[int] = None
    explanation: Optional[str] = None
    score: Optional[int] = None
    summary: Optional[str] = None

class AlignmentResultResponse(AlignmentResultBase, BaseDomainSchema):
    pass

