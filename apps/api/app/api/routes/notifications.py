from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationUpdate
from app.repositories.notification_repository import notification_repo

router = APIRouter()


@router.get("", response_model=list[NotificationResponse])
async def get_notifications(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notifications for current developer user.
    Returns unread notifications first, ordered by creation date.
    """
    notifications = await notification_repo.get_by_developer(
        db=db,
        developer_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return notifications


@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get count of unread notifications for current user.
    """
    notifications = await notification_repo.get_unread_by_developer(
        db=db,
        developer_id=current_user.id,
        skip=0,
        limit=10000
    )
    return {"unread_count": len(notifications)}


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: UUID,
    notification_in: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read.
    Only the recipient (developer) can mark it as read.
    """
    notification = await notification_repo.get(db=db, id=notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.developer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify notification that does not belong to you"
        )

    notification = await notification_repo.mark_as_read(db=db, notification_id=notification_id)
    return notification


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a notification.
    Only the recipient (developer) can delete it.
    """
    notification = await notification_repo.get(db=db, id=notification_id)

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.developer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete notification that does not belong to you"
        )

    await notification_repo.delete(db=db, id=notification_id)
    return {"message": "Notification deleted successfully"}
