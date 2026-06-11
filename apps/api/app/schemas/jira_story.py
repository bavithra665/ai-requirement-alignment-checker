from typing import Optional, List, Any, Dict
from uuid import UUID
from pydantic import BaseModel
from app.schemas.base import BaseDomainSchema


class JiraStoryBase(BaseModel):
    project_id: UUID
    jira_issue_key: str
    title: str
    description: Optional[str] = None
    status: str
    story_type: Optional[str] = None
    epic_key: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    external_url: Optional[str] = None
    labels: Optional[List[str]] = None


class JiraStoryCreate(JiraStoryBase):
    pass


class JiraStoryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    story_type: Optional[str] = None
    epic_key: Optional[str] = None
    assignee: Optional[str] = None
    priority: Optional[str] = None
    external_url: Optional[str] = None
    labels: Optional[List[str]] = None


class JiraStoryResponse(JiraStoryBase, BaseDomainSchema):
    pass
