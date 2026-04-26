# v1.0 - 用户身份层模型：users / user_wx_auth / natural_persons / enterprises
from sqlalchemy import Column, String, DateTime, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(16), nullable=False, unique=True)
    password_hash = Column(String(128), nullable=False)
    # 角色：W / C / B / A / BROKER / DRIVER / WAREHOUSE_KEEPER
    role = Column(String(32), nullable=False)
    status = Column(String(16), nullable=False, default="active")
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('W','C','B','A','BROKER','DRIVER','WAREHOUSE_KEEPER')", name="chk_users_role"),
        CheckConstraint("status IN ('active','suspended','deleted')", name="chk_users_status"),
    )


class UserWxAuth(Base):
    # 微信认证表，支持多商户小程序（每个 appid 对应独立 open_id）
    __tablename__ = "user_wx_auth"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    mini_program_appid = Column(String(64), nullable=False)
    open_id = Column(String(64), nullable=False)
    union_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class NaturalPerson(Base):
    # 自然人档案（供应商/经纪人/司机/仓管员实名主体）
    __tablename__ = "natural_persons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 一个 user 只能有一个自然人档案
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    real_name = Column(String(64), nullable=False)
    id_card_no = Column(String(18), nullable=True)
    id_card_front_oss = Column(String(512), nullable=True)
    id_card_back_oss = Column(String(512), nullable=True)
    auth_status = Column(String(16), nullable=False, default="pending")
    auth_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("auth_status IN ('pending','verified','failed')", name="chk_natural_persons_auth_status"),
    )


class Enterprise(Base):
    # 企业档案（终端收购商C / 贸易收购商B 注册主体）
    __tablename__ = "enterprises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 一个 user 只能有一个企业档案
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    credit_code = Column(String(32), nullable=True, unique=True)
    legal_person = Column(String(64), nullable=True)
    license_oss = Column(String(512), nullable=True)
    auth_status = Column(String(16), nullable=False, default="pending")
    auth_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("auth_status IN ('pending','verified','failed')", name="chk_enterprises_auth_status"),
    )
