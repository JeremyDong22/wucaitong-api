# v1.1 - 合同层模型：contracts / contract_signatures
# 修复：ContractSignature 添加 UniqueConstraint(contract_id, signer_id) 防止重复签章
from sqlalchemy import Column, String, DateTime, Numeric, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Contract(Base):
    # 电子合同（系统在 WAREHOUSED 后自动生成，双方签章）
    # order_id 不建外键，避免与 purchase_orders.contract_id 循环引用
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_no = Column(String(64), nullable=False, unique=True)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), nullable=False)
    seller_id = Column(UUID(as_uuid=True), nullable=False)
    product_name = Column(String(128), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=True)
    unit_price = Column(Numeric(15, 4), nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=True)
    contract_pdf_oss = Column(String(512), nullable=True)
    status = Column(String(16), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('pending','signed','cancelled')", name="chk_contract_status"),
    )


class ContractSignature(Base):
    # 签章记录（买方和卖方各签一次，同一人不能重复签同一合同）
    __tablename__ = "contract_signatures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), nullable=False)
    signer_id = Column(UUID(as_uuid=True), nullable=False)
    signer_role = Column(String(32), nullable=False)
    # 签章图片 OSS 路径
    signature_oss = Column(String(512), nullable=True)
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        # 同一合同同一签章人只能签一次
        UniqueConstraint("contract_id", "signer_id", name="uq_contract_signature"),
    )
