# v1.0 - 运输层模型：transport_tasks / gps_checkpoints
from sqlalchemy import Column, String, DateTime, Numeric, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class TransportTask(Base):
    # 运输任务（一个订单对应一个运输任务）
    __tablename__ = "transport_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    driver_id = Column(UUID(as_uuid=True), nullable=False)
    plate_no = Column(String(16), nullable=False)
    # 路线信息（预留，可存起点/终点坐标）
    route = Column(JSON, nullable=True)
    status = Column(String(16), nullable=False, default="assigned")
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('assigned','departed','arrived_source','source_weighed',"
            "'in_transit','arrived_warehouse','completed','cancelled')",
            name="chk_transport_task_status"
        ),
    )


class GpsCheckpoint(Base):
    # GPS 打卡记录（司机出发/到达供应商/到达仓库）
    __tablename__ = "gps_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transport_task_id = Column(UUID(as_uuid=True), nullable=False)
    # depart=出发, arrive_source=到达供应商处, arrive_warehouse=到达仓库
    checkpoint_type = Column(String(16), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "checkpoint_type IN ('depart','arrive_source','arrive_warehouse')",
            name="chk_gps_type"
        ),
    )
