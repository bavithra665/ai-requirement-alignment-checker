from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationRepository:
    def __init__(self):
        self.model = Notification

    async def get(self, db: AsyncSession, id: UUID) -> Optional[Notification]:
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unread_by_developer(
        self, db: AsyncSession, developer_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        stmt = (
            select(self.model)
            .where(self.model.developer_id == developer_id, self.model.is_read == False)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_developer(
        self, db: AsyncSession, developer_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        stmt = (
            select(self.model)
            .where(self.model.developer_id == developer_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: NotificationCreate) -> Notification:
        db_obj = self.model(**obj_in.dict())
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def mark_as_read(self, db: AsyncSession, notification_id: UUID) -> Optional[Notification]:
        stmt = select(self.model).where(self.model.id == notification_id)
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            db.add(notification)
            await db.commit()
            await db.refresh(notification)

        return notification

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        notification = result.scalar_one_or_none()

        if notification:
            await db.delete(notification)
            await db.commit()
            return True

        return False


notification_repo = NotificationRepository()
