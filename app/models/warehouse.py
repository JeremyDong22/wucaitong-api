# v1.0 - 入库层模型：warehouses / warehouse_receipts
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Warehouse(Base):
    # 仓库（C 或 B 均可管理自己的仓库）
    __tablename__ = "warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(128), nullable=False)
    address = Column(String(256), nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active','inactive')", name="chk_warehouse_status"),
    )


class WarehouseReceipt(Base):
    # 入库验收单（仓管员签收后生成）
    __tablename__ = "warehouse_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False)
    keeper_id = Column(UUID(as_uuid=True), nullable=False)
    product_category_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    actual_weight = Column(Numeric(15, 3), nullable=False)
    # 库位号（货物存放位置）
    location = Column(String(64), nullable=True)
    signed = Column(Boolean, nullable=False, default=False)
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
