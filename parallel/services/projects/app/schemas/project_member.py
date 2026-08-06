from pydantic import BaseModel


class ProjectMemberCreate(BaseModel):
    user_id: str
    role: str = "Member"


class ProjectMemberResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str

    model_config = {
        "from_attributes": True,
    }
