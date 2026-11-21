import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


class Base(DeclarativeBase):
    pass


class WorkflowJobRecord(Base):
    __tablename__ = "scholarai_workflow_jobs"

    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    current_node: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    agent_status: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    student_profile: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    profile_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    profile_valid: Mapped[bool] = mapped_column(default=False, nullable=False)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def _database_url() -> str | None:
    url = (
        os.getenv("SUPABASE_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or ""
    ).strip()
    if not url or "YOUR_" in url.upper() or "[PASSWORD]" in url:
        return None
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = _database_url()
engine = (
    create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
    if DATABASE_URL
    else None
)

if engine is not None:
    Base.metadata.create_all(engine)


def timestamp(value: datetime | None = None) -> datetime:
    return value or datetime.now(timezone.utc)


def create_job(job_id: str, state: dict[str, Any]) -> None:
    if engine is None:
        return
    now = timestamp()
    with Session(engine) as session:
        session.add(
            WorkflowJobRecord(
                job_id=job_id,
                status="queued",
                current_node="",
                agent_status=dict(state.get("agent_status", {})),
                student_profile=dict(state.get("student_profile", {})),
                profile_urls=list(state.get("profile_urls", [])),
                profile_valid=bool(state.get("profile_valid", False)),
                result=None,
                events=[],
                errors=[],
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()


def update_job(job_id: str, updates: dict[str, Any]) -> None:
    if engine is None:
        return
    with Session(engine) as session:
        record = session.get(WorkflowJobRecord, job_id)
        if record is None:
            return
        for key, value in updates.items():
            if hasattr(record, key) and key not in {"job_id", "created_at"}:
                setattr(record, key, value)
        record.updated_at = timestamp()
        session.commit()


def get_job(job_id: str) -> dict[str, Any] | None:
    if engine is None:
        return None
    with Session(engine) as session:
        record = session.get(WorkflowJobRecord, job_id)
        if record is None:
            return None
        return {
            "job_id": record.job_id,
            "status": record.status,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "agent_status": record.agent_status or {},
            "student_profile": record.student_profile or {},
            "profile_urls": record.profile_urls or [],
            "profile_valid": record.profile_valid,
            "current_node": record.current_node,
            "events": record.events or [],
            "result": record.result,
            "errors": record.errors or [],
        }
