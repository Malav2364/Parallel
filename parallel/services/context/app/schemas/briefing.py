from pydantic import BaseModel


class BriefingItem(BaseModel):
    repo: str | None = None
    number: int | None = None
    title: str | None = None
    url: str | None = None


class BriefingResponse(BaseModel):
    connected: bool
    review_requests: int
    my_open_prs: int
    message: str
    review_requests_items: list[BriefingItem]
    my_pr_items: list[BriefingItem]
