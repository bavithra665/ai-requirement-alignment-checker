from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel


class PullRequest(Base, BaseDomainModel):
    __tablename__ = "pull_requests"

    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False, index=True)
    repository_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    pr_description = Column(Text, nullable=True)     # PR body/description
    diff_content = Column(Text, nullable=True)        # raw diff (optional, may be large)
    status = Column(String, nullable=False)           # open, closed, merged

    # Extended metadata
    author = Column(String, nullable=True)
    branch = Column(String, nullable=True)            # head branch
    base_branch = Column(String, nullable=True)       # target branch
    head_sha = Column(String, nullable=True)          # head commit SHA
    merged_at = Column(DateTime(timezone=True), nullable=True)
    changed_files = Column(JSONB, nullable=True)      # list of changed file paths

    # Relationships
    project = relationship("Project", back_populates="pull_requests")
    code_artifacts = relationship("CodeArtifact", back_populates="pull_request", cascade="all, delete-orphan")
