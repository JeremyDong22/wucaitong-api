# v1.0 - 采购公告与认售模型：purchase_announcements / supply_commitments
from sqlalchemy import Column, String, DateTime, Numeric, Date, JSON, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class PurchaseAnnouncement(Base):
    # 采购公告（C 或 B 发布，供应商 A 认售）
    __tablename__ = "purchase_announcements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), nullable=False)
    product_category_id = Column(UUID(as_uuid=True), nullable=False)
    product_name = Column(String(128), nullable=True)
    specification = Column(JSON, nullable=True)
    grade = Column(String(64), nullable=True)
    unit_price = Column(Numeric(15, 4), nullable=False)
    quantity = Column(Numeric(15, 3), nullable=False)
    # 剩余可认售数量，随认售确认递减
    remaining_quantity = Column(Numeric(15, 3), nullable=False, default=0)
    deadline = Column(Date, nullable=False)
    # BUYER=买方派车, SELLER=卖方自行送货
    transport_arrangement = Column(String(16), nullable=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("transport_arrangement IN ('BUYER','SELLER')", name="chk_announcement_transport"),
        CheckConstraint("status IN ('active','paused','closed')", name="chk_announcement_status"),
    )


class SupplyCommitment(Base):
    # 认售记录（供应商 A 响应采购公告）
    __tablename__ = "supply_commitments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    announcement_id = Column(UUID(as_uuid=True), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), nullable=False)
    # 可选：经纪人代填时关联经纪人
    broker_id = Column(UUID(as_uuid=True), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    expected_delivery_date = Column(Date, nullable=True)
    status = Column(String(16), nullable=False, default="pending")
    confirmed_by = Column(UUID(as_uuid=True), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('pending','confirmed','rejected')", name="chk_commitment_status"),
    )
