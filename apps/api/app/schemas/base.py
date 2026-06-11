from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class BaseDomainSchema(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    created_by_id: Optional[UUID] = None
    updated_by_id: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)
