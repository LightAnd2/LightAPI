from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, Index
from db.models import Base


class DeployEvent(Base):
    __tablename__ = "deploy_events"

    id = Column(String, primary_key=True)
    endpoint_id = Column(String, ForeignKey("endpoints.id"), nullable=True)
    repo = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    commit_sha = Column(String, nullable=False)
    commit_message = Column(Text, nullable=True)
    pusher = Column(String, nullable=True)
    deployed_at = Column(DateTime, default=datetime.utcnow)
    pre_deploy_baseline_ms = Column(Float, nullable=True)
    post_deploy_baseline_ms = Column(Float, nullable=True)
    regression_detected = Column(Boolean, nullable=True)
    regression_percent = Column(Float, nullable=True)
    analysis_complete = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_deploy_endpoint", "endpoint_id", "deployed_at"),
    )
