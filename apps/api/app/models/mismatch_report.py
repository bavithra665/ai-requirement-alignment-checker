from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseDomainModel

class MismatchReport(Base, BaseDomainModel):
    __tablename__ = "mismatch_reports"

    project_id = Column(UUID(as_uuid=True), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    alignment_result_id = Column(UUID(as_uuid=True), ForeignKey('alignment_results.id', ondelete='CASCADE'), nullable=False, index=True)
    
    mismatch_type = Column(String, nullable=False) # e.g. "missing_implementation", "logic_error"
    description = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    
    # Reporting layer fields
    status = Column(String, nullable=False, default="Open")          # Open / Reviewed / Resolved
    severity = Column(String, nullable=False, default="Medium")      # Critical / High / Medium / Low
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="mismatch_reports")
    alignment_result = relationship("AlignmentResult", backref="mismatch_reports")
