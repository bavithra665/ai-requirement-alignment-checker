from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema


class PullRequestBase(BaseModel):
    project_id: UUID
    pr_number: int
    repository_url: str
    title: str
    pr_description: Optional[str] = None
    diff_content: Optional[str] = None
    status: str
    author: Optional[str] = None
    branch: Optional[str] = None
    base_branch: Optional[str] = None
    head_sha: Optional[str] = None
    merged_at: Optional[datetime] = None
    changed_files: Optional[List[str]] = None


class PullRequestCreate(PullRequestBase):
    pass


class PullRequestUpdate(BaseModel):
    title: Optional[str] = None
    pr_description: Optional[str] = None
    diff_content: Optional[str] = None
    status: Optional[str] = None
    author: Optional[str] = None
    branch: Optional[str] = None
    base_branch: Optional[str] = None
    head_sha: Optional[str] = None
    merged_at: Optional[datetime] = None
    changed_files: Optional[List[str]] = None


class PullRequestResponse(PullRequestBase, BaseDomainSchema):
    pass
