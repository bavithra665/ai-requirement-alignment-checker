from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        stmt = select(self.model).where(self.model.is_deleted == False).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType, created_by_id: Optional[UUID] = None) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        if hasattr(db_obj, "created_by_id") and created_by_id:
            db_obj.created_by_id = created_by_id
            db_obj.updated_by_id = created_by_id
            
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        updated_by_id: Optional[UUID] = None
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        if hasattr(db_obj, "updated_by_id") and updated_by_id:
            db_obj.updated_by_id = updated_by_id

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: UUID, updated_by_id: Optional[UUID] = None) -> ModelType:
        # Soft delete
        from datetime import datetime, timezone
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        db_obj = result.scalar_one_or_none()
        
        if db_obj and hasattr(db_obj, "is_deleted"):
            db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now(timezone.utc)
            if updated_by_id and hasattr(db_obj, "updated_by_id"):
                db_obj.updated_by_id = updated_by_id
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj
