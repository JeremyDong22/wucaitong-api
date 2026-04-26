# v1.1 - 商户端（C/B）请求/响应 Schema
# 修复：transport_arrangement 改用 Literal 类型，强制枚举值与数据库 CHECK 约束一致（BUYER/SELLER）
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from datetime import date


class AnnouncementCreate(BaseModel):
    product_category_id: UUID
    product_name: Optional[str] = None
    specification: Optional[Dict[str, Any]] = None
    grade: Optional[str] = None
    unit_price: float
    quantity: float
    deadline: date
    # 强制枚举：BUYER=买方派车, SELLER=卖方自行送货
    transport_arrangement: Literal["BUYER", "SELLER"] = "BUYER"


class AnnouncementResponse(BaseModel):
    id: UUID
    product_category_id: UUID
    product_name: Optional[str]
    unit_price: float
    quantity: float
    remaining_quantity: float
    deadline: date
    status: str

    class Config:
        from_attributes = True


class ConfirmCommitmentRequest(BaseModel):
    commitment_id: UUID
    approved: bool


class WeighbridgeRecordRequest(BaseModel):
    record_type: str          # source or warehouse
    gross_weight: float
    tare_weight: float
    deduction: Optional[float] = 0.0


class WarehouseReceiptRequest(BaseModel):
    warehouse_id: UUID
    quantity: float
    actual_weight: float
    location: Optional[str] = None


class OrderResponse(BaseModel):
    id: UUID
    order_no: str
    order_type: str
    status: str
    buyer_merchant_id: UUID
    seller_merchant_id: Optional[UUID]
    seller_supplier_id: Optional[UUID]
    quantity: float
    unit_price: float
    total_amount: float
    created_at: str

    class Config:
        from_attributes = True


class DispatchRequest(BaseModel):
    driver_id: UUID
    plate_no: str


class BrokerTaskCreate(BaseModel):
    broker_id: UUID
    product_category_id: UUID
    product_name: Optional[str] = None
    quantity: float
    unit_price: Optional[float] = None
    deadline: Optional[date] = None


class SupplierAdmitRequest(BaseModel):
    user_phone: str
    product_category_id: Optional[UUID] = None


class InviteRequest(BaseModel):
    user_phone: str
    role: str   # DRIVER, BROKER, WAREHOUSE_KEEPER


class PayRequest(BaseModel):
    channel: str = "wechat"  # 支付渠道
