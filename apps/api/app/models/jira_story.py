from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel


class JiraStory(Base, BaseDomainModel):
    __tablename__ = "jira_stories"

    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    jira_issue_key = Column(String, nullable=False, index=True)  # e.g. PROJ-123
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    story_type = Column(String, nullable=True)        # Story, Epic, Task, Bug
    epic_key = Column(String, nullable=True, index=True)
    assignee = Column(String, nullable=True)
    priority = Column(String, nullable=True)          # Highest, High, Medium, Low, Lowest
    external_url = Column(String, nullable=True)      # direct link to Jira issue
    labels = Column(JSONB, nullable=True)             # list of string labels

    # Relationships
    project = relationship("Project", back_populates="jira_stories")
