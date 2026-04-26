# v1.1 - 商户档案层模型：merchants / brokers / broker_merchant_relations /
#         drivers / driver_merchant_relations / warehouse_keepers
# 修复：Broker 和 Driver 添加 UniqueConstraint(user_id)，防止同一用户创建多个档案
from sqlalchemy import Column, String, DateTime, Boolean, JSON, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Merchant(Base):
    # 商户档案（终端收购商C 或 贸易收购商B）
    __tablename__ = "merchants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), nullable=False)
    # merchant_type: C=终端收购商, B=贸易收购商
    merchant_type = Column(String(8), nullable=False)
    sub_domain = Column(String(64), nullable=True, unique=True)
    logo_oss = Column(String(512), nullable=True)
    primary_color = Column(String(16), nullable=True)
    # 允许经营的品种大类 ID 列表（JSON array）
    allowed_product_categories = Column(JSON, nullable=True)
    status = Column(String(16), nullable=False, default="pending")
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("merchant_type IN ('C','B')", name="chk_merchants_type"),
        CheckConstraint("status IN ('pending','active','suspended')", name="chk_merchants_status"),
    )


class Broker(Base):
    # 经纪人档案（不绑定单一商户，通过 broker_merchant_relations 建立多对多关系）
    __tablename__ = "brokers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    natural_person_id = Column(UUID(as_uuid=True), nullable=False)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active','suspended')", name="chk_brokers_status"),
        # 一个用户只能有一个经纪人档案
        UniqueConstraint("user_id", name="uq_brokers_user_id"),
    )


class BrokerMerchantRelation(Base):
    # 经纪人-商户多对多关系（C 或 B 均可邀请经纪人）
    __tablename__ = "broker_merchant_relations"

    broker_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    merchant_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    invited_by = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active','inactive')", name="chk_broker_merchant_status"),
    )


class Driver(Base):
    # 司机档案（不绑定单一商户，通过 driver_merchant_relations 建立多对多关系）
    __tablename__ = "drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    natural_person_id = Column(UUID(as_uuid=True), nullable=False)
    license_no = Column(String(32), nullable=True)
    license_photo_oss = Column(String(512), nullable=True)
    status = Column(String(16), nullable=False, default="pending")
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('pending','verified','active','suspended')", name="chk_drivers_status"),
        # 一个用户只能有一个司机档案
        UniqueConstraint("user_id", name="uq_drivers_user_id"),
    )


class DriverMerchantRelation(Base):
    # 司机-商户多对多关系
    __tablename__ = "driver_merchant_relations"

    driver_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    merchant_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True)
    invited_by = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active','inactive')", name="chk_driver_merchant_status"),
    )


class WarehouseKeeper(Base):
    # 仓管员（C 或 B 均可管理，merchant_id 标识归属）
    __tablename__ = "warehouse_keepers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    natural_person_id = Column(UUID(as_uuid=True), nullable=False)
    merchant_id = Column(UUID(as_uuid=True), nullable=False)
    warehouse_id = Column(UUID(as_uuid=True), nullable=True)
    sign_authorized = Column(Boolean, nullable=False, default=False)
    status = Column(String(16), nullable=False, default="active")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('active','suspended')", name="chk_warehouse_keepers_status"),
    )
