# v1.0 - 平台管理端（W）请求/响应 Schema
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class ProductCategoryCreate(BaseModel):
    category_code: str
    category_name: str
    sub_category: Optional[str] = None
    spec_template: Optional[dict] = None
    grade_options: Optional[List[str]] = None
    tax_code: Optional[str] = None
    tax_rate: Optional[float] = None
    unit: str = "ton"
    is_hazardous: bool = False


class ProductCategoryResponse(BaseModel):
    id: UUID
    category_code: str
    category_name: str
    unit: str
    status: str

    class Config:
        from_attributes = True


class MerchantApproveRequest(BaseModel):
    approved: bool
    reason: Optional[str] = None  # 拒绝原因


class MerchantResponse(BaseModel):
    id: UUID
    merchant_type: str
    sub_domain: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True


class BindMerchantRelationRequest(BaseModel):
    upstream_merchant_id: UUID    # 贸易收购商 B
    downstream_merchant_id: UUID  # 终端收购商 C
    product_category_id: UUID     # 绑定品种（B的品种必须 ⊆ C的品种）


class MerchantRelationResponse(BaseModel):
    id: UUID
    upstream_merchant_id: UUID
    downstream_merchant_id: UUID
    product_category_id: UUID
    status: str

    class Config:
        from_attributes = True
