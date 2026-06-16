import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class NotificationType(str, Enum):
    CLIENT_REJECTED = "client_rejected"
    CLIENT_REQUESTED_CHANGES = "client_requested_changes"
    CLIENT_APPROVED = "client_approved"


class NotificationCreate(BaseModel):
    developer_id: uuid.UUID
    project_id: uuid.UUID
    requirement_version_id: Optional[uuid.UUID] = None
    notification_type: NotificationType
    message: str


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class NotificationResponse(BaseModel):
    id: uuid.UUID
    developer_id: uuid.UUID
    project_id: uuid.UUID
    requirement_version_id: Optional[uuid.UUID]
    notification_type: NotificationType
    message: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
