from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel

class ClientApproval(Base, BaseDomainModel):
    __tablename__ = "client_approvals"

    requirement_version_id = Column(UUID(as_uuid=True), ForeignKey('requirement_versions.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(String, nullable=False) # e.g. "approved", "rejected", "pending"
    comments = Column(String, nullable=True)
    
    # Relationships
    requirement_version = relationship("RequirementVersion", back_populates="approvals")
