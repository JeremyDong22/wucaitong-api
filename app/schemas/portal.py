# v1.0 - 门户端（供应商A / 经纪人 / 司机 / 仓管员）请求/响应 Schema
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CommitSupplyRequest(BaseModel):
    quantity: float
    expected_delivery_date: Optional[str] = None


class GpsCheckinRequest(BaseModel):
    checkpoint_type: str   # depart / arrive_source / arrive_warehouse
    latitude: float
    longitude: float
    recorded_at: Optional[datetime] = None


class UploadEvidenceRequest(BaseModel):
    related_type: str      # weighbridge / transport / warehouse
    file_type: str         # image / video / pdf
    oss_url: str


class BrokerTaskAcceptResponse(BaseModel):
    task_no: str
    status: str

    class Config:
        from_attributes = True


class FillSupplierRequest(BaseModel):
    supplier_phone: str
    quantity: float
    expected_delivery_date: Optional[str] = None


class WarehouseReceiptSignRequest(BaseModel):
    receipt_id: UUID
    # 签章后上传签名图片
    signature_oss: Optional[str] = None
