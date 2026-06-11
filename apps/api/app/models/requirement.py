from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel

class Requirement(Base, BaseDomainModel):
    __tablename__ = "requirements"

    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="requirements")
    versions = relationship("RequirementVersion", back_populates="requirement", cascade="all, delete-orphan")
