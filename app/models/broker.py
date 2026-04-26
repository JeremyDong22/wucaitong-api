# v1.0 - 经纪人任务模型：broker_tasks
from sqlalchemy import Column, String, DateTime, Numeric, Date, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class BrokerTask(Base):
    # 经纪人任务（商户创建订单时选择经纪人协助，生成此任务）
    __tablename__ = "broker_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_no = Column(String(64), nullable=False, unique=True)
    merchant_id = Column(UUID(as_uuid=True), nullable=False)
    broker_id = Column(UUID(as_uuid=True), nullable=False)
    product_category_id = Column(UUID(as_uuid=True), nullable=False)
    product_name = Column(String(128), nullable=True)
    specification = Column(JSON, nullable=True)
    grade = Column(String(64), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit_price = Column(Numeric(15, 4), nullable=True)
    deadline = Column(Date, nullable=True)
    status = Column(String(16), nullable=False, default="pending")
    accepted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','accepted','processing','completed')",
            name="chk_broker_task_status"
        ),
    )
