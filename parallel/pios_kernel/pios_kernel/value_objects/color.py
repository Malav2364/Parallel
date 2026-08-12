from pydantic import BaseModel


class Color(BaseModel):
    hex: str
