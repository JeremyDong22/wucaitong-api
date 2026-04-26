# v1.0 - 消息层模型：notifications
from sqlalchemy import Column, String, DateTime, Boolean, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Notification(Base):
    # 站内消息通知（配合微信订阅消息和短信通知使用）
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(128), nullable=False)
    content = Column(Text, nullable=False)
    # order / payment / transport / system
    type = Column(String(32), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('order','payment','transport','system')", name="chk_notification_type"),
    )
