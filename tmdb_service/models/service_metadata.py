from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import Session

from tmdb_service.globals import Base


class ServiceMetadata(Base):
    __tablename__ = "service_metadata"

    key: Mapped[str] = mapped_column(String, primary_key=True, autoincrement=False)
    value: Mapped[str] = mapped_column(String)
    updated_at: Mapped[datetime] = mapped_column(DateTime)


def set_metadata(session: Session, key: str, value: str):
    obj = session.get(ServiceMetadata, key)
    now = datetime.now(timezone.utc)
    if obj:
        obj.value = value
        obj.updated_at = now
    else:
        obj = ServiceMetadata(key=key, value=value, updated_at=now)
        session.add(obj)


def get_metadata(session: Session, key: str):
    obj = session.get(ServiceMetadata, key)
    return obj.value if obj else None
