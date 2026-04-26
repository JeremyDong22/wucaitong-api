# v1.0 - 商品字典层模型：product_categories / merchant_relations / merchant_supplier_relations
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class ProductCategory(Base):
    # 品种大类字典，由平台 W 维护
    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_code = Column(String(32), nullable=False, unique=True)
    category_name = Column(String(64), nullable=False)
    sub_category = Column(String(64), nullable=True)
    # 规格模板（JSON）：定义该品种支持的规格字段
    spec_template = Column(JSON, nullable=True)
    # 品级选项（JSON array）：如 ["一级品","二级品","废料"]
    grade_options = Column(JSON, nullable=True)
    tax_code = Column(String(32), nullable=True)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    unit = Column(String(16), nullable=False, default="ton")
    is_hazardous = Column(Boolean, nullable=False, default=False)
    status = Column(String(16), nullable=False, default="active")
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active','inactive')", name="chk_product_categories_status"),
    )


class MerchantRelation(Base):
    # C-B 交易关系绑定（W 配置），按品种大类粒度，B 的品种必须 ⊆ C 的品种
    __tablename__ = "merchant_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # upstream=B（贸易收购商），downstream=C（终端收购商）
    upstream_merchant_id = Column(UUID(as_uuid=True), nullable=False)
    downstream_merchant_id = Column(UUID(as_uuid=True), nullable=False)
    product_category_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(16), nullable=False, default="active")
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("upstream_merchant_id", "downstream_merchant_id", "product_category_id",
                         name="uq_merchant_relations"),
        CheckConstraint("status IN ('active','suspended')", name="chk_merchant_relations_status"),
    )


class MerchantSupplierRelation(Base):
    # 商户-供应商准入关系（C 或 B 自行准入供应商 A）
    __tablename__ = "merchant_supplier_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    merchant_id = Column(UUID(as_uuid=True), nullable=False)
    supplier_id = Column(UUID(as_uuid=True), nullable=False)
    product_category_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("merchant_id", "supplier_id", name="uq_merchant_supplier"),
        CheckConstraint("status IN ('active','blocked')", name="chk_merchant_supplier_status"),
    )
