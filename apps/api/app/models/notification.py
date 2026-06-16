import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class NotificationType(str, enum.Enum):
    CLIENT_REJECTED = "client_rejected"
    CLIENT_REQUESTED_CHANGES = "client_requested_changes"
    CLIENT_APPROVED = "client_approved"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    developer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_version_id = Column(UUID(as_uuid=True), ForeignKey("requirement_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    developer = relationship("User", foreign_keys=[developer_id])
    project = relationship("Project", foreign_keys=[project_id])
    requirement_version = relationship("RequirementVersion", foreign_keys=[requirement_version_id])
