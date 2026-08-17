from fastapi import APIRouter, Depends, Header

from app.api.deps import get_habit_service
from app.schemas.habit import HabitCreate, HabitResponse
from app.services.habit_service import HabitService


router = APIRouter()


@router.post(
    "",
    response_model=HabitResponse,
    status_code=201,
)
def create_habit(
    request: HabitCreate,
    x_user_id: str = Header(...),
    service: HabitService = Depends(get_habit_service),
) -> HabitResponse:
    return service.create_habit(
        request=request,
        owner_id=x_user_id,
    )


@router.get(
    "",
    response_model=list[HabitResponse],
)
def list_habits(
    x_user_id: str = Header(...),
    service: HabitService = Depends(get_habit_service),
) -> list[HabitResponse]:
    return service.list_habits(x_user_id)


@router.get(
    "/{habit_id}",
    response_model=HabitResponse,
)
def get_habit(
    habit_id: str,
    service: HabitService = Depends(get_habit_service),
) -> HabitResponse:
    habit = service.get_habit(habit_id)

    if habit is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Habit not found",
        )

    return habit