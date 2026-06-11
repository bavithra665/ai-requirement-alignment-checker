import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin, declared_attr

@declarative_mixin
class BaseDomainModel:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def created_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    @declared_attr
    def updated_by_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
