# v1.0 - 开票层模型：invoices / reverse_invoice_charges
from sqlalchemy import Column, String, DateTime, Numeric, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Invoice(Base):
    # 发票记录（REVERSE=反向开票给供应商A, FORWARD=正向开票给终端商C）
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_no = Column(String(64), nullable=False, unique=True)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    seller_id = Column(UUID(as_uuid=True), nullable=False)
    buyer_id = Column(UUID(as_uuid=True), nullable=False)
    # REVERSE=反向开票, FORWARD=正向开票
    invoice_type = Column(String(16), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    invoice_pdf_oss = Column(String(512), nullable=True)
    status = Column(String(16), nullable=False, default="pending")
    # 第三方开票 API 请求 ID（百望云等）
    api_request_id = Column(String(128), nullable=True)
    api_response = Column(Text, nullable=True)
    issued_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("invoice_type IN ('REVERSE','FORWARD')", name="chk_invoice_type"),
        CheckConstraint("status IN ('pending','issued','failed')", name="chk_invoice_status"),
    )


class ReverseInvoiceCharge(Base):
    # 反向开票服务费记录（平台唯一收费项，费率由开票 API 返回）
    __tablename__ = "reverse_invoice_charges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), nullable=False)
    merchant_id = Column(UUID(as_uuid=True), nullable=False)
    invoice_amount = Column(Numeric(15, 2), nullable=False)
    charge_amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(16), nullable=False, default="pending")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('pending','paid')", name="chk_charge_status"),
    )
