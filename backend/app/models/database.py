"""SQLite persistent storage via SQLAlchemy with transactional audit logging."""

import datetime as dt
import json
from typing import Any, Generator
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    target = Column(String(32), default="web", nullable=False)
    status = Column(String(32), default="running", nullable=False)
    cwd = Column(String(256), default="/repo")
    config_json = Column(Text, default="{}")
    summary_json = Column(Text, default="{}")
    step_count = Column(Integer, default=0)
    artifact_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)


class StepModel(Base):
    __tablename__ = "steps"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    step_index = Column(Integer, nullable=False)
    action = Column(String(64), nullable=False)
    selector = Column(String(256), nullable=True)
    status = Column(String(32), default="passed", nullable=False)
    duration_ms = Column(Float, default=0.0)
    input_json = Column(Text, default="{}")
    output_json = Column(Text, default="{}")
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String(64), primary_key=True, index=True)
    session_id = Column(String(64), index=True, nullable=False)
    step_id = Column(String(64), index=True, nullable=False)
    artifact_type = Column(String(64), nullable=False)
    mime_type = Column(String(64), nullable=False)
    content = Column(Text, nullable=False)
    size_bytes = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)


class AuditModel(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=False)
    details_json = Column(Text, default="{}")
    ip_address = Column(String(64), default="127.0.0.1")
    timestamp = Column(DateTime, default=utcnow)


class EvaluationModel(Base):
    __tablename__ = "evaluations"

    id = Column(String(64), primary_key=True, index=True)
    benchmark_name = Column(String(128), nullable=False)
    target = Column(String(32), default="web")
    total_scenarios = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    ambiguity_resolution_rate = Column(Float, nullable=False)
    latency_p95_ms = Column(Float, nullable=False)
    results_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=utcnow)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
