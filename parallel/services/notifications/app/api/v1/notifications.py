from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_notification_service
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)
from app.services.notification_service import NotificationService


router = APIRouter()


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=201,
)
def create_notification(
    request: NotificationCreate,
    x_user_id: str = Header(...),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> NotificationResponse:
    return service.create_notification(
        request=request,
        owner_id=x_user_id,
    )


@router.get(
    "",
    response_model=list[NotificationResponse],
)
def list_notifications(
    x_user_id: str = Header(...),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> list[NotificationResponse]:
    return service.list_notifications(x_user_id)


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification(
    notification_id: str,
    x_user_id: str = Header(...),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> NotificationResponse:
    notification = service.get_notification(
        notification_id=notification_id,
        owner_id=x_user_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return notification


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read(
    notification_id: str,
    x_user_id: str = Header(...),
    service: NotificationService = Depends(
        get_notification_service,
    ),
) -> NotificationResponse:
    notification = service.mark_as_read(
        notification_id=notification_id,
        owner_id=x_user_id,
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return notification