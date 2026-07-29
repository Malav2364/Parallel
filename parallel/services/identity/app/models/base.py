from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.mixins import UUIDMixin


class BaseModel(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    __abstract__ = True