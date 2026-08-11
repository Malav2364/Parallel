from pydantic import BaseModel


class ProjectActivityUpdate(BaseModel):
    current_focus: str | None = None
    latest_activity: str | None = None
    