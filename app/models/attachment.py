# v1.0 - 附件层模型：attachments（统一存储所有业务媒体文件）
from sqlalchemy import Column, String, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Attachment(Base):
    # 统一附件表（磅单照片/运输凭证/入库验收图片等均存此表）
    # 通过 related_type + related_id 关联到具体业务记录
    __tablename__ = "attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    # 关联业务类型：weighbridge / transport / warehouse / contract / invoice
    related_type = Column(String(32), nullable=False)
    related_id = Column(UUID(as_uuid=True), nullable=False)
    uploader_id = Column(UUID(as_uuid=True), nullable=False)
    uploader_role = Column(String(32), nullable=False)
    # image / video / pdf
    file_type = Column(String(16), nullable=True)
    oss_url = Column(String(512), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("file_type IN ('image','video','pdf')", name="chk_attachment_type"),
    )
