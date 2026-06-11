from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel

class AlignmentResult(Base, BaseDomainModel):
    __tablename__ = "alignment_results"

    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    requirement_version_id = Column(UUID(as_uuid=True), ForeignKey('requirement_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    jira_story_id = Column(UUID(as_uuid=True), ForeignKey('jira_stories.id', ondelete='SET NULL'), nullable=True, index=True)
    pull_request_id = Column(UUID(as_uuid=True), ForeignKey('pull_requests.id', ondelete='SET NULL'), nullable=True, index=True)
    code_artifact_id = Column(UUID(as_uuid=True), ForeignKey('code_artifacts.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Relationship scores
    requirement_jira_score = Column(Integer, nullable=True)  # 0-100 similarity
    jira_pr_score = Column(Integer, nullable=True)           # 0-100 similarity
    pr_artifact_score = Column(Integer, nullable=True)       # 0-100 similarity
    overall_alignment_score = Column(Integer, nullable=False) # computed overall alignment score
    
    alignment_status = Column(String, nullable=False, default="Aligned")  # Aligned, Potential Drift, Misaligned
    confidence = Column(Integer, nullable=False, default=100)            # 0-100
    explanation = Column(Text, nullable=True)                             # Groq narrative explanation
    
    # Legacy score field (for compatibility, maps to overall_alignment_score)
    score = Column(Integer, nullable=False)
    summary = Column(Text, nullable=True) # maps to explanation
    
    # Relationships
    project = relationship("Project", back_populates="alignment_results")
    requirement_version = relationship("RequirementVersion")
    jira_story = relationship("JiraStory")
    pull_request = relationship("PullRequest")
    code_artifact = relationship("CodeArtifact")

