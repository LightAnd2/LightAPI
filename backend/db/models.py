import os
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lightai.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    _migrate_add_workspace_column()


def _migrate_add_workspace_column():
    """Add endpoints.workspace_id to databases created before workspaces existed."""
    from sqlalchemy import text
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(endpoints)"))]
        if cols and "workspace_id" not in cols:
            conn.execute(text("ALTER TABLE endpoints ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'demo'"))
            conn.commit()


class DirectoryApi(Base):
    """A public API in the discovery directory (sourced from public-apis)."""
    __tablename__ = "directory_apis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text, default="")
    auth = Column(String, default="None")
    https = Column(Boolean, default=False)
    cors = Column(String, default="unknown")
    category = Column(String, nullable=False, index=True)

    __table_args__ = (
        Index("idx_directory_category_name", "category", "name"),
    )


class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, nullable=False, default="demo", index=True)
    url = Column(String, nullable=False)
    name = Column(String, nullable=False)
    check_interval = Column(Integer, default=30)
    alert_threshold = Column(Integer, default=500)
    webhook_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    readings = relationship("Reading", back_populates="endpoint", cascade="all, delete-orphan")
    incidents = relationship("Incident", back_populates="endpoint", cascade="all, delete-orphan")
    anomaly_events = relationship("AnomalyEvent", back_populates="endpoint", cascade="all, delete-orphan")
    model_info = relationship("EndpointModel", back_populates="endpoint", uselist=False, cascade="all, delete-orphan")


class Reading(Base):
    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    latency_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=False)

    endpoint = relationship("Endpoint", back_populates="readings")

    __table_args__ = (
        Index("idx_readings_endpoint_timestamp", "endpoint_id", "timestamp"),
    )


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    peak_latency = Column(Float, nullable=True)
    severity = Column(String, default="warning")
    is_resolved = Column(Boolean, default=False)

    endpoint = relationship("Endpoint", back_populates="incidents")


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    confidence = Column(Float, nullable=False)
    predicted_latency = Column(Float, nullable=True)
    actual_latency = Column(Float, nullable=False)

    endpoint = relationship("Endpoint", back_populates="anomaly_events")


class EndpointModel(Base):
    __tablename__ = "endpoint_models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), unique=True, nullable=False)
    model_path = Column(String, nullable=True)
    scaler_path = Column(String, nullable=True)
    last_trained = Column(DateTime, nullable=True)
    readings_count = Column(Integer, default=0)
    is_ready = Column(Boolean, default=False)

    endpoint = relationship("Endpoint", back_populates="model_info")
