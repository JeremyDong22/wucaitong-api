# v1.0 - 支付层模型：payments
from sqlalchemy import Column, String, DateTime, Numeric, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Payment(Base):
    # 支付记录（对接在线支付 API，含幂等键防重复扣款）
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_no = Column(String(64), nullable=False, unique=True)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    payer_id = Column(UUID(as_uuid=True), nullable=False)
    payee_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    # GOODS_PAYMENT=货款, SERVICE_FEE=服务费
    payment_type = Column(String(16), nullable=False)
    # 幂等键，防止重复提交支付请求
    idempotency_key = Column(String(128), nullable=False, unique=True)
    status = Column(String(16), nullable=False, default="pending")
    channel = Column(String(32), nullable=True)
    # 支付渠道交易流水号
    channel_trade_no = Column(String(128), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    failed_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("payment_type IN ('GOODS_PAYMENT','SERVICE_FEE')", name="chk_payment_type"),
        CheckConstraint("status IN ('pending','success','failed')", name="chk_payment_status"),
    )
