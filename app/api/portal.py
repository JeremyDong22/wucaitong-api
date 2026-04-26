# v1.1 - 门户端 API（供应商A / 经纪人 / 司机 / 仓管员）
# 修复：
#   - list_my_orders 补充 seller_merchant_id 查询，避免供应商以商户身份下单时查不到
#   - confirm_warehouse_receipt 校验仓管员归属（只能操作本商户的订单）
#   - 所有列表接口加 skip/limit 分页
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.order_service import transition_order
from app.models.user import User, NaturalPerson
from app.models.announcement import PurchaseAnnouncement, SupplyCommitment
from app.models.order import PurchaseOrder
from app.models.broker import BrokerTask
from app.models.transport import TransportTask, GpsCheckpoint
from app.models.weighbridge import WeighbridgeRecord
from app.models.warehouse import WarehouseReceipt
from app.models.contract import Contract, ContractSignature
from app.models.attachment import Attachment
from app.schemas.portal import (
    CommitSupplyRequest, GpsCheckinRequest, UploadEvidenceRequest,
    FillSupplierRequest, WarehouseReceiptSignRequest,
)

router = APIRouter(prefix="/portal", tags=["门户端"])

require_supplier = require_role("A")
require_broker = require_role("BROKER")
require_driver = require_role("DRIVER")
require_keeper = require_role("WAREHOUSE_KEEPER")


# ── 供应商：认售 ──────────────────────────────────────────────────────────────

@router.get("/announcements")
async def list_announcements(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查看所有有效采购公告（分页）"""
    result = await db.execute(
        select(PurchaseAnnouncement)
        .where(PurchaseAnnouncement.status == "active")
        .order_by(PurchaseAnnouncement.created_at.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/announcements/{announcement_id}/commit")
async def commit_supply(
    announcement_id: UUID,
    body: CommitSupplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_supplier),
):
    """供应商认售"""
    ann_result = await db.execute(
        select(PurchaseAnnouncement).where(
            PurchaseAnnouncement.id == announcement_id,
            PurchaseAnnouncement.status == "active",
        )
    )
    announcement = ann_result.scalar_one_or_none()
    if not announcement:
        raise HTTPException(status_code=404, detail="公告不存在或已关闭")

    if float(announcement.remaining_quantity) < body.quantity:
        raise HTTPException(status_code=400, detail="认售数量超过剩余可供量")

    person_result = await db.execute(
        select(NaturalPerson).where(NaturalPerson.user_id == current_user.id)
    )
    person = person_result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=400, detail="请先完成实名认证")

    from datetime import date as date_type
    commitment = SupplyCommitment(
        announcement_id=announcement_id,
        supplier_id=person.id,
        quantity=body.quantity,
        expected_delivery_date=date_type.fromisoformat(body.expected_delivery_date)
        if body.expected_delivery_date else None,
        status="pending",
    )
    db.add(commitment)
    await db.commit()
    return {"message": "认售已提交，等待收购商确认"}


# ── 供应商：查看订单 / 签章 ───────────────────────────────────────────────────

@router.get("/orders")
async def list_my_orders(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查看我的订单（供应商视角）

    修复：同时查询 seller_supplier_id（自然人）和 seller_merchant_id（商户身份），
    避免商户身份作为卖方时订单查不到。
    """
    person_result = await db.execute(
        select(NaturalPerson).where(NaturalPerson.user_id == current_user.id)
    )
    person = person_result.scalar_one_or_none()

    conditions = []
    if person:
        conditions.append(PurchaseOrder.seller_supplier_id == person.id)

    if not conditions:
        return []

    result = await db.execute(
        select(PurchaseOrder)
        .where(or_(*conditions))
        .order_by(PurchaseOrder.created_at.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/orders/{order_id}/contract/sign")
async def sign_contract(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """供应商/仓管员签章（UniqueConstraint 保证同一人不重复签）"""
    order_result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "CONTRACT_PENDING":
        raise HTTPException(status_code=400, detail="订单不在待签章状态")

    contract_result = await db.execute(select(Contract).where(Contract.order_id == order_id))
    contract = contract_result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    # 记录签章（数据库 UniqueConstraint 会拒绝重复签章）
    sig = ContractSignature(
        contract_id=contract.id,
        signer_id=current_user.id,
        signer_role=current_user.role,
        signed_at=datetime.utcnow(),
    )
    db.add(sig)

    # 检查是否双方都已签章
    sigs_result = await db.execute(
        select(ContractSignature).where(ContractSignature.contract_id == contract.id)
    )
    all_sigs = sigs_result.scalars().all()
    if len(all_sigs) >= 2:  # 买卖双方各签一次
        contract.status = "signed"
        await transition_order(order, "CONTRACTED", current_user.id, current_user.role, db)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="您已完成签章，请勿重复操作")
    return {"message": "签章完成"}


# ── 经纪人：任务管理 ──────────────────────────────────────────────────────────

@router.get("/broker/tasks")
async def list_broker_tasks(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """经纪人任务列表（分页）"""
    from app.models.merchant import Broker
    broker_result = await db.execute(select(Broker).where(Broker.user_id == current_user.id))
    broker = broker_result.scalar_one_or_none()
    if not broker:
        return []

    result = await db.execute(
        select(BrokerTask)
        .where(BrokerTask.broker_id == broker.id)
        .order_by(BrokerTask.created_at.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/broker/tasks/{task_id}/accept")
async def accept_broker_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """接受经纪人任务"""
    result = await db.execute(select(BrokerTask).where(BrokerTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status != "pending":
        raise HTTPException(status_code=400, detail="任务状态不可接受")

    task.status = "accepted"
    task.accepted_at = datetime.utcnow()
    await db.commit()
    return {"message": "任务已接受"}


@router.post("/broker/tasks/{task_id}/suppliers")
async def fill_supplier_for_task(
    task_id: UUID,
    body: FillSupplierRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_broker),
):
    """经纪人代填供应商信息"""
    task_result = await db.execute(select(BrokerTask).where(BrokerTask.id == task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.status not in ["accepted", "processing"]:
        raise HTTPException(status_code=400, detail="任务不在可操作状态")

    supplier_result = await db.execute(select(User).where(User.phone == body.supplier_phone))
    supplier_user = supplier_result.scalar_one_or_none()
    if not supplier_user:
        raise HTTPException(status_code=404, detail="供应商手机号未注册")

    person_result = await db.execute(
        select(NaturalPerson).where(NaturalPerson.user_id == supplier_user.id)
    )
    person = person_result.scalar_one_or_none()
    if not person:
        raise HTTPException(status_code=400, detail="供应商未完成实名认证")

    task.status = "processing"
    await db.commit()
    return {"message": "供应商信息已填写，等待商户确认"}


# ── 司机：GPS打卡 / 上传证据 ──────────────────────────────────────────────────

@router.post("/driver/tasks/{order_id}/checkin")
async def gps_checkin(
    order_id: UUID,
    body: GpsCheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_driver),
):
    """GPS打卡（出发/到达供应商/到达仓库）"""
    transport_result = await db.execute(
        select(TransportTask).where(TransportTask.order_id == order_id)
    )
    transport = transport_result.scalar_one_or_none()
    if not transport:
        raise HTTPException(status_code=404, detail="运输任务不存在")

    checkpoint = GpsCheckpoint(
        transport_task_id=transport.id,
        checkpoint_type=body.checkpoint_type,
        latitude=body.latitude,
        longitude=body.longitude,
        recorded_at=body.recorded_at or datetime.utcnow(),
    )
    db.add(checkpoint)

    order_result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id))
    order = order_result.scalar_one_or_none()
    if order:
        status_map = {
            "depart":           "DISPATCHED",
            "arrive_source":    "ARRIVED_SOURCE",
            "arrive_warehouse": "ARRIVED_WAREHOUSE",
        }
        if next_status := status_map.get(body.checkpoint_type):
            try:
                await transition_order(order, next_status, current_user.id, current_user.role, db)
            except HTTPException:
                pass  # 状态已正确则忽略

    await db.commit()
    return {"message": "GPS打卡成功"}


@router.post("/driver/tasks/{order_id}/upload")
async def upload_evidence(
    order_id: UUID,
    body: UploadEvidenceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_driver),
):
    """司机上传磅单照片等证据"""
    order_result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    attachment = Attachment(
        tenant_id=order.tenant_id,
        related_type=body.related_type,
        related_id=order_id,
        uploader_id=current_user.id,
        uploader_role=current_user.role,
        file_type=body.file_type,
        oss_url=body.oss_url,
    )
    db.add(attachment)
    await db.commit()
    return {"message": "证据已上传"}


# ── 仓管员：入库验收 ──────────────────────────────────────────────────────────

@router.get("/warehouse/tasks")
async def list_warehouse_tasks(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_keeper),
):
    """仓管员待入库任务列表（只返回本商户的订单）"""
    from app.models.warehouse import WarehouseKeeper as WKModel
    keeper_result = await db.execute(
        select(WKModel).where(WKModel.user_id == current_user.id)
    )
    keeper = keeper_result.scalar_one_or_none()
    if not keeper:
        return []

    # 只显示本商户（keeper.merchant_id）的待入库订单
    result = await db.execute(
        select(PurchaseOrder).where(
            PurchaseOrder.tenant_id == keeper.merchant_id,
            PurchaseOrder.status.in_(["ARRIVED_WAREHOUSE", "WAREHOUSE_WEIGHED"]),
        )
        .order_by(PurchaseOrder.created_at.desc())
        .offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/warehouse/tasks/{order_id}/receipt")
async def confirm_warehouse_receipt(
    order_id: UUID,
    body: WarehouseReceiptSignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_keeper),
):
    """仓管员入库验收签章（校验仓管员必须属于该订单的商户）"""
    from app.models.warehouse import WarehouseKeeper as WKModel

    # 查当前仓管员档案
    keeper_result = await db.execute(
        select(WKModel).where(WKModel.user_id == current_user.id)
    )
    keeper = keeper_result.scalar_one_or_none()
    if not keeper:
        raise HTTPException(status_code=403, detail="您没有仓管员权限")

    receipt_result = await db.execute(
        select(WarehouseReceipt).where(WarehouseReceipt.order_id == order_id)
    )
    receipt = receipt_result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="入库单不存在")

    order_result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == order_id))
    order = order_result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 校验仓管员归属：只能操作本商户的订单
    if order.tenant_id != keeper.merchant_id:
        raise HTTPException(status_code=403, detail="无权操作其他商户的订单")

    receipt.signed = True
    receipt.signed_at = datetime.utcnow()

    if order.status == "WAREHOUSING":
        await transition_order(order, "WAREHOUSED", current_user.id, current_user.role, db)

        # 自动生成合同
        contract = Contract(
            contract_no=f"CON-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}",
            order_id=order_id,
            buyer_id=order.buyer_merchant_id,
            seller_id=order.seller_supplier_id or order.seller_merchant_id,
            product_name=order.product_name,
            quantity=receipt.actual_weight,
            unit_price=order.unit_price,
            total_amount=float(receipt.actual_weight) * float(order.unit_price),
            status="pending",
        )
        db.add(contract)
        await db.flush()

        order.contract_id = contract.id
        await transition_order(order, "CONTRACT_PENDING", current_user.id, current_user.role, db)

    await db.commit()
    return {"message": "入库验收完成，合同已生成，等待双方签章"}
