from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.deps import get_reminder_service
from app.schemas.reminder import (
    ReminderCreate,
    ReminderResponse,
    ReminderUpdate,
)
from app.services.reminder_service import ReminderService


router = APIRouter()


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=201,
)
def create_reminder(
    request: ReminderCreate,
    x_user_id: str = Header(...),
    service: ReminderService = Depends(
        get_reminder_service
    ),
) -> ReminderResponse:

    return service.create_reminder(
        request=request,
        owner_id=x_user_id,
    )


@router.get(
    "",
    response_model=list[ReminderResponse],
)
def list_reminders(
    x_user_id: str = Header(...),
    service: ReminderService = Depends(
        get_reminder_service
    ),
) -> list[ReminderResponse]:

    return service.list_reminders(
        x_user_id
    )


@router.get(
    "/{reminder_id}",
    response_model=ReminderResponse,
)
def get_reminder(
    reminder_id: str,
    service: ReminderService = Depends(
        get_reminder_service
    ),
) -> ReminderResponse:

    reminder = service.get_reminder(
        reminder_id
    )

    if reminder is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )

    return reminder


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
)
def update_reminder(
    reminder_id: str,
    request: ReminderUpdate,
    service: ReminderService = Depends(
        get_reminder_service
    ),
) -> ReminderResponse:

    reminder = service.update_reminder(
        reminder_id,
        request,
    )

    if reminder is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )

    return reminder


@router.delete(
    "/{reminder_id}",
    status_code=204,
)
def delete_reminder(
    reminder_id: str,
    service: ReminderService = Depends(
        get_reminder_service
    ),
) -> None:

    deleted = service.delete_reminder(
        reminder_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )