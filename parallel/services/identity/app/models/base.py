from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDMixin


class BaseModel(
    UUIDMixin,
    TimestampMixin,
    Base,
):
    __abstract__ = True
