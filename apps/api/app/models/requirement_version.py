from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel

class RequirementVersion(Base, BaseDomainModel):
    __tablename__ = "requirement_versions"

    requirement_id = Column(UUID(as_uuid=True), ForeignKey('requirements.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    change_summary = Column(String, nullable=True)
    ai_summary = Column(Text, nullable=True)
    status = Column(String, default="Draft", nullable=False)
    is_baseline = Column(Boolean, default=False, nullable=False)

    # Relationships
    requirement = relationship("Requirement", back_populates="versions")
    approvals = relationship("ClientApproval", back_populates="requirement_version", cascade="all, delete-orphan")
