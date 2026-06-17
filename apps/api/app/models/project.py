from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel

class Project(Base, BaseDomainModel):
    __tablename__ = "projects"

    name = Column(String, nullable=False, index=True)
    client_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    repository_url = Column(String, nullable=True)
    jira_project_key = Column(String, nullable=True)    
    owner_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)

    # Relationships
    owner = relationship("User", back_populates="projects", foreign_keys=[owner_id])
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    jira_stories = relationship("JiraStory", back_populates="project", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequest", back_populates="project", cascade="all, delete-orphan")
    alignment_results = relationship("AlignmentResult", back_populates="project", cascade="all, delete-orphan")
    mismatch_reports = relationship("MismatchReport", back_populates="project", cascade="all, delete-orphan")
