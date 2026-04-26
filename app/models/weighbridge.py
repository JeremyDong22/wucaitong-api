# v1.1 - 过磅层模型：weighbridge_records（唯一重量数据源）
# 修复：添加 UniqueConstraint(order_id, record_type) 防止同一订单重复录入同类型磅单
from sqlalchemy import Column, String, DateTime, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class WeighbridgeRecord(Base):
    # 磅单记录（司机在源头和仓库各上传一次，为重量唯一数据源）
    __tablename__ = "weighbridge_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    # source=源头过磅, warehouse=仓库复磅
    record_type = Column(String(16), nullable=False)
    gross_weight = Column(Numeric(15, 3), nullable=False)
    tare_weight = Column(Numeric(15, 3), nullable=False)
    net_weight = Column(Numeric(15, 3), nullable=False)
    # 扣杂量（含水分/杂质等扣减）
    deduction = Column(Numeric(15, 3), nullable=True)
    # 实际结算重量 = net_weight - deduction
    actual_weight = Column(Numeric(15, 3), nullable=True)
    recorded_by = Column(UUID(as_uuid=True), nullable=False)
    recorded_by_role = Column(String(32), nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("record_type IN ('source','warehouse')", name="chk_weighbridge_type"),
        # 同一订单每种类型只能有一条记录（源头磅 + 仓库复磅各一次）
        UniqueConstraint("order_id", "record_type", name="uq_weighbridge_order_type"),
    )
