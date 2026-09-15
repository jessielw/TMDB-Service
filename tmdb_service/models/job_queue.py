from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from tmdb_service.db_utils import Base


class JobQueue(Base):
    """Schema declaration for the PostgreSQL-backed worker queue."""

    __tablename__ = "job_queue"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'failed')",
            name="job_queue_status_check",
        ),
        Index("job_queue_status_created_idx", "status", "created_at", "id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    job_type: Mapped[str] = mapped_column(Text)
    payload: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str] = mapped_column(Text, server_default="queued", default="queued")
    attempts: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    last_error: Mapped[str | None] = mapped_column(Text, default=None)
