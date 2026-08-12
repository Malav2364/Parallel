from pydantic import BaseModel


class SpaceProjectCreate(BaseModel):
    project_id: str


class SpaceProjectResponse(BaseModel):
    id: str
    space_id: str
    project_id: str
