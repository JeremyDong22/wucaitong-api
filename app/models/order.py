# v1.1 - 订单层模型：purchase_orders / order_status_logs
# 修复：添加 committed_at 字段（认售确认时间戳）
# 订单类型：DIRECT（直采C←A）/ TRADE（贸易C←B）/ SUB（子订单B←A）
from sqlalchemy import Column, String, DateTime, Numeric, JSON, Text, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

# 合法状态转换映射（业务层校验使用）
ORDER_TRANSITIONS = {
    "DRAFT":              ["COMMITTED", "CANCELLED"],
    "COMMITTED":          ["DISPATCHED", "ARRIVED_WAREHOUSE", "CANCELLED"],
    "DISPATCHED":         ["ARRIVED_SOURCE", "CANCELLED"],
    "ARRIVED_SOURCE":     ["SOURCE_WEIGHED"],
    "SOURCE_WEIGHED":     ["IN_TRANSIT"],
    "IN_TRANSIT":         ["ARRIVED_WAREHOUSE"],
    "ARRIVED_WAREHOUSE":  ["WAREHOUSE_WEIGHED", "CONTRACT_PENDING"],
    "WAREHOUSE_WEIGHED":  ["WAREHOUSING", "CONTRACT_PENDING"],
    "WAREHOUSING":        ["WAREHOUSED"],
    "WAREHOUSED":         ["CONTRACT_PENDING"],
    "CONTRACT_PENDING":   ["CONTRACTED"],
    "CONTRACTED":         ["PAYING"],
    "PAYING":             ["PAID"],
    "PAID":               ["COMPLETED"],
}

VALID_STATUSES = [
    "DRAFT", "COMMITTED", "DISPATCHED", "ARRIVED_SOURCE", "SOURCE_WEIGHED",
    "IN_TRANSIT", "ARRIVED_WAREHOUSE", "WAREHOUSE_WEIGHED", "WAREHOUSING",
    "WAREHOUSED", "CONTRACT_PENDING", "CONTRACTED", "PAYING", "PAID",
    "COMPLETED", "CANCELLED",
]


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    order_no = Column(String(64), nullable=False, unique=True)
    # DIRECT=直采, TRADE=贸易主订单, SUB=贸易子订单
    order_type = Column(String(16), nullable=False)
    parent_order_id = Column(UUID(as_uuid=True), nullable=True)
    # 经纪人任务关联（可空）
    broker_task_id = Column(UUID(as_uuid=True), nullable=True)

    # 买方始终是商户（C 或 B）
    buyer_merchant_id = Column(UUID(as_uuid=True), nullable=False)
    # 卖方二选一：TRADE 订单填 seller_merchant_id（B），DIRECT/SUB 填 seller_supplier_id（A）
    seller_merchant_id = Column(UUID(as_uuid=True), nullable=True)
    seller_supplier_id = Column(UUID(as_uuid=True), nullable=True)

    product_category_id = Column(UUID(as_uuid=True), nullable=False)
    product_name = Column(String(128), nullable=True)
    specification = Column(JSON, nullable=True)
    grade = Column(String(64), nullable=True)
    quantity = Column(Numeric(15, 3), nullable=False)
    unit = Column(String(16), nullable=False, default="ton")
    unit_price = Column(Numeric(15, 4), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)

    # 贸易链路：SUB 订单标识最终流向的 C 商户
    resale_to_merchant_id = Column(UUID(as_uuid=True), nullable=True)

    # 运输安排
    transport_arrangement = Column(String(16), nullable=True)
    driver_id = Column(UUID(as_uuid=True), nullable=True)
    plate_no = Column(String(16), nullable=True)

    # 物流节点时间戳（过磅数据统一从 weighbridge_records 查询）
    committed_at = Column(DateTime, nullable=True)       # 认售确认时间
    dispatched_at = Column(DateTime, nullable=True)
    arrived_source_at = Column(DateTime, nullable=True)
    source_weighed_at = Column(DateTime, nullable=True)
    in_transit_at = Column(DateTime, nullable=True)
    arrived_warehouse_at = Column(DateTime, nullable=True)
    warehouse_weighed_at = Column(DateTime, nullable=True)
    warehousing_at = Column(DateTime, nullable=True)
    warehoused_at = Column(DateTime, nullable=True)

    # 合同 ID（不建外键，避免与 contracts.order_id 循环引用）
    contract_id = Column(UUID(as_uuid=True), nullable=True)
    paid_at = Column(DateTime, nullable=True)

    status = Column(String(32), nullable=False, default="DRAFT")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("order_type IN ('DIRECT','TRADE','SUB')", name="chk_order_type"),
        CheckConstraint("transport_arrangement IN ('BUYER','SELLER')", name="chk_transport_arrangement"),
        CheckConstraint(
            "status IN ('DRAFT','COMMITTED','DISPATCHED','ARRIVED_SOURCE','SOURCE_WEIGHED',"
            "'IN_TRANSIT','ARRIVED_WAREHOUSE','WAREHOUSE_WEIGHED','WAREHOUSING',"
            "'WAREHOUSED','CONTRACT_PENDING','CONTRACTED','PAYING','PAID','COMPLETED','CANCELLED')",
            name="chk_order_status"
        ),
    )


class OrderStatusLog(Base):
    # 订单状态变更审计日志（不可篡改）
    __tablename__ = "order_status_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), nullable=False)
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)
    operator_id = Column(UUID(as_uuid=True), nullable=False)
    operator_role = Column(String(32), nullable=False)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
