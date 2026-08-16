from fastapi import APIRouter, Depends, Header

from app.api.deps import get_goal_service
from app.schemas.goal import GoalCreate, GoalResponse
from app.services import GoalService

router = APIRouter()


@router.post("", response_model=GoalResponse, status_code=201)
def create_goal(
    request: GoalCreate,
    x_user_id: str = Header(...),
    service: GoalService = Depends(get_goal_service),
) -> GoalResponse:
    return service.create_goal(request, x_user_id)


@router.get("", response_model=list[GoalResponse])
def list_goals(
    x_user_id: str = Header(...),
    service: GoalService = Depends(get_goal_service),
) -> list[GoalResponse]:
    return service.list_goals(x_user_id)
